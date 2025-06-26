# skill_system/detector.py
"""
OpenCV-based Skill Detection System

This module handles all visual detection aspects of the skill system including:
- Template matching for skill icons
- Cooldown overlay detection
- Skill bar mapping and monitoring
- State change detection
"""

import cv2
import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Set
from PIL import Image, ImageGrab
import logging

from .skill_types import (
    VisualSkill, SkillState, SkillPosition, SkillBarMapping,
    DetectionResult, DetectionMethod, DetectionConfig
)


class SkillDetector:
    """Advanced OpenCV-based skill detection system"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Detection cache for performance
        self._template_cache: Dict[str, np.ndarray] = {}
        self._position_cache: Dict[str, SkillPosition] = {}
        self._detection_cache: Dict[str, DetectionResult] = {}
        
        # Performance monitoring
        self._detection_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Detection settings
        self.default_config = DetectionConfig()
        
        # Screen capture optimization
        self._last_screenshot = None
        self._last_screenshot_time = 0.0
        self._screenshot_cache_duration = 0.05  # 50ms cache
        
    def load_skill_template(self, skill: VisualSkill) -> bool:
        """Load and cache skill icon template"""
        if not skill.icon_path:
            return False
            
        try:
            # Check cache first
            cache_key = f"{skill.name}_{skill.icon_path}"
            if cache_key in self._template_cache:
                skill.icon_template = self._template_cache[cache_key]
                self._cache_hits += 1
                return True
            
            # Load image
            template = cv2.imread(skill.icon_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"Failed to load template: {skill.icon_path}")
                return False
                
            # Convert to RGB for consistency
            template = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            
            # Cache template
            self._template_cache[cache_key] = template
            skill.icon_template = template
            self._cache_misses += 1
            
            self.logger.debug(f"Loaded template for {skill.name}: {template.shape}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading template for {skill.name}: {e}")
            return False
    
    def capture_screen_region(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Capture screen region with caching optimization"""
        try:
            current_time = time.time()
            
            # Use cached screenshot if recent enough
            if (self._last_screenshot is not None and 
                current_time - self._last_screenshot_time < self._screenshot_cache_duration):
                x, y, w, h = region
                return self._last_screenshot[y:y+h, x:x+w]
            
            # Capture new screenshot
            screenshot = ImageGrab.grab()
            screenshot_array = np.array(screenshot)
            
            # Cache full screenshot
            self._last_screenshot = screenshot_array
            self._last_screenshot_time = current_time
            
            # Return requested region
            x, y, w, h = region
            return screenshot_array[y:y+h, x:x+w]
            
        except Exception as e:
            self.logger.error(f"Screen capture failed: {e}")
            return None
    
    def detect_skill_in_region(self, skill: VisualSkill, region: Tuple[int, int, int, int],
                              config: Optional[DetectionConfig] = None) -> DetectionResult:
        """Detect skill in specific screen region"""
        start_time = time.time()
        config = config or skill.detection_config or self.default_config
        
        # Ensure template is loaded
        if skill.icon_template is None:
            if not self.load_skill_template(skill):
                return DetectionResult(
                    position=SkillPosition(0, region),
                    detected_skill=None,
                    state=SkillState.UNKNOWN,
                    confidence=0.0,
                    detection_time=time.time() - start_time,
                    method_used=DetectionMethod.TEMPLATE_MATCH
                )
        
        # Capture screen region
        screen_region = self.capture_screen_region(region)
        if screen_region is None:
            return self._create_failed_result(skill, region, start_time)
        
        # Try different detection methods
        best_result = None
        best_confidence = 0.0
        
        for method in config.detection_methods:
            if method == DetectionMethod.TEMPLATE_MATCH:
                result = self._detect_by_template_match(skill, screen_region, region, config)
            elif method == DetectionMethod.COOLDOWN_OVERLAY:
                result = self._detect_cooldown_overlay(skill, screen_region, region, config)
            elif method == DetectionMethod.COLOR_ANALYSIS:
                result = self._detect_by_color_analysis(skill, screen_region, region, config)
            else:
                continue
                
            if result.confidence > best_confidence:
                best_result = result
                best_confidence = result.confidence
        
        # Update detection time
        if best_result:
            best_result.detection_time = time.time() - start_time
            self._detection_times.append(best_result.detection_time)
            
            # Keep only last 100 detection times for performance monitoring
            if len(self._detection_times) > 100:
                self._detection_times.pop(0)
        
        return best_result or self._create_failed_result(skill, region, start_time)
    
    def _detect_by_template_match(self, skill: VisualSkill, screen_region: np.ndarray,
                                region: Tuple[int, int, int, int], 
                                config: DetectionConfig) -> DetectionResult:
        """Detect skill using template matching"""
        try:
            template = skill.icon_template
            if template is None:
                return self._create_failed_result(skill, region, time.time())
            
            # Perform template matching
            if config.use_multi_scale:
                best_confidence, best_state = self._multi_scale_template_match(
                    screen_region, template, config
                )
            else:
                result = cv2.matchTemplate(screen_region, template, cv2.TM_CCOEFF_NORMED)
                _, best_confidence, _, _ = cv2.minMaxLoc(result)
                best_state = self._analyze_template_match_state(screen_region, template, best_confidence)
            
            # Determine skill state based on confidence and analysis
            if best_confidence >= config.template_threshold:
                state = best_state
            else:
                state = SkillState.UNAVAILABLE
                
            return DetectionResult(
                position=SkillPosition(0, region),
                detected_skill=skill,
                state=state,
                confidence=best_confidence,
                detection_time=0.0,  # Will be set by caller
                method_used=DetectionMethod.TEMPLATE_MATCH
            )
            
        except Exception as e:
            self.logger.error(f"Template matching failed for {skill.name}: {e}")
            return self._create_failed_result(skill, region, time.time())
    
    def _multi_scale_template_match(self, screen_region: np.ndarray, template: np.ndarray,
                                  config: DetectionConfig) -> Tuple[float, SkillState]:
        """Perform template matching at multiple scales"""
        best_confidence = 0.0
        best_state = SkillState.UNKNOWN
        
        min_scale, max_scale = config.scale_range
        scales = np.linspace(min_scale, max_scale, 5)
        
        for scale in scales:
            # Resize template
            new_width = int(template.shape[1] * scale)
            new_height = int(template.shape[0] * scale)
            
            if new_width <= 0 or new_height <= 0:
                continue
                
            scaled_template = cv2.resize(template, (new_width, new_height))
            
            # Skip if template is larger than screen region
            if (scaled_template.shape[0] > screen_region.shape[0] or 
                scaled_template.shape[1] > screen_region.shape[1]):
                continue
                
            # Perform matching
            result = cv2.matchTemplate(screen_region, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, _ = cv2.minMaxLoc(result)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_state = self._analyze_template_match_state(
                    screen_region, scaled_template, confidence
                )
        
        return best_confidence, best_state
    
    def _analyze_template_match_state(self, screen_region: np.ndarray, template: np.ndarray,
                                    confidence: float) -> SkillState:
        """Analyze template match to determine skill state"""
        try:
            if confidence < 0.7:
                return SkillState.UNAVAILABLE
            
            # Find the best match location
            result = cv2.matchTemplate(screen_region, template, cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc = cv2.minMaxLoc(result)
            
            # Extract the matched region
            h, w = template.shape[:2]
            matched_region = screen_region[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
            
            # Analyze for cooldown overlay (darker overlay indicates cooldown)
            gray_matched = cv2.cvtColor(matched_region, cv2.COLOR_RGB2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
            
            # Calculate brightness difference
            matched_brightness = np.mean(gray_matched)
            template_brightness = np.mean(gray_template)
            brightness_ratio = matched_brightness / template_brightness
            
            # If significantly darker, likely on cooldown
            if brightness_ratio < 0.7:
                return SkillState.COOLDOWN
            elif brightness_ratio > 0.9:
                return SkillState.READY
            else:
                return SkillState.UNKNOWN
                
        except Exception as e:
            self.logger.error(f"State analysis failed: {e}")
            return SkillState.UNKNOWN
    
    def _detect_cooldown_overlay(self, skill: VisualSkill, screen_region: np.ndarray,
                               region: Tuple[int, int, int, int],
                               config: DetectionConfig) -> DetectionResult:
        """Detect cooldown overlay on skill icon"""
        try:
            # Convert to grayscale for overlay detection
            gray_region = cv2.cvtColor(screen_region, cv2.COLOR_RGB2GRAY)
            
            # Look for dark overlay patterns typical of cooldowns
            # This involves checking for semi-transparent dark overlays
            
            # Calculate histogram to detect darkness level
            hist = cv2.calcHist([gray_region], [0], None, [256], [0, 256])
            
            # Normalize histogram
            hist = hist.flatten() / hist.sum()
            
            # Check concentration in darker values (0-100)
            dark_concentration = np.sum(hist[0:100])
            
            # Determine state based on darkness
            if dark_concentration > 0.6:  # More than 60% dark pixels
                state = SkillState.COOLDOWN
                confidence = min(dark_concentration, config.cooldown_threshold + 0.2)
            else:
                state = SkillState.READY
                confidence = 1.0 - dark_concentration
            
            return DetectionResult(
                position=SkillPosition(0, region),
                detected_skill=skill,
                state=state,
                confidence=confidence,
                detection_time=0.0,
                method_used=DetectionMethod.COOLDOWN_OVERLAY
            )
            
        except Exception as e:
            self.logger.error(f"Cooldown overlay detection failed: {e}")
            return self._create_failed_result(skill, region, time.time())
    
    def _detect_by_color_analysis(self, skill: VisualSkill, screen_region: np.ndarray,
                                region: Tuple[int, int, int, int],
                                config: DetectionConfig) -> DetectionResult:
        """Detect skill state by color analysis"""
        try:
            # Convert to HSV for better color analysis
            hsv_region = cv2.cvtColor(screen_region, cv2.COLOR_RGB2HSV)
            
            # Analyze saturation and brightness
            saturation = hsv_region[:, :, 1]
            brightness = hsv_region[:, :, 2]
            
            avg_saturation = np.mean(saturation)
            avg_brightness = np.mean(brightness)
            
            # Skills on cooldown typically have reduced saturation and brightness
            if avg_saturation < 100 and avg_brightness < 100:
                state = SkillState.COOLDOWN
                confidence = 0.7
            else:
                state = SkillState.READY
                confidence = 0.8
            
            return DetectionResult(
                position=SkillPosition(0, region),
                detected_skill=skill,
                state=state,
                confidence=confidence,
                detection_time=0.0,
                method_used=DetectionMethod.COLOR_ANALYSIS
            )
            
        except Exception as e:
            self.logger.error(f"Color analysis failed: {e}")
            return self._create_failed_result(skill, region, time.time())
    
    def scan_skill_bar(self, skill_bar_mapping: SkillBarMapping,
                      skills_to_detect: List[VisualSkill],
                      config: Optional[DetectionConfig] = None) -> Dict[int, DetectionResult]:
        """Scan entire skill bar for skill positions and states"""
        config = config or self.default_config
        results = {}
        
        try:
            self.logger.debug(f"Scanning skill bar with {len(skills_to_detect)} skills")
            
            for slot_index, slot_region in enumerate(skill_bar_mapping.slot_regions):
                best_result = None
                best_confidence = 0.0
                
                # Test each skill template against this slot
                for skill in skills_to_detect:
                    if not skill.enabled or skill.icon_template is None:
                        continue
                    
                    result = self.detect_skill_in_region(skill, slot_region, config)
                    
                    if result.confidence > best_confidence:
                        best_result = result
                        best_confidence = result.confidence
                        
                        # Update skill position if found
                        if result.confidence >= config.template_threshold:
                            skill.position = SkillPosition(slot_index, slot_region)
                
                if best_result and best_result.confidence >= config.template_threshold:
                    results[slot_index] = best_result
                    
                    # Update skill bar mapping
                    skill_bar_mapping.detected_skills[slot_index] = best_result.detected_skill
            
            skill_bar_mapping.update_scan_time()
            self.logger.debug(f"Skill bar scan completed. Found {len(results)} skills.")
            
        except Exception as e:
            self.logger.error(f"Skill bar scan failed: {e}")
        
        return results
    
    def monitor_skill_states(self, skills: Dict[str, VisualSkill],
                           config: Optional[DetectionConfig] = None) -> Dict[str, SkillState]:
        """Monitor current states of positioned skills"""
        config = config or self.default_config
        states = {}
        
        for skill_name, skill in skills.items():
            if not skill.position or not skill.enabled:
                continue
                
            try:
                result = self.detect_skill_in_region(skill, skill.position.region, config)
                if result.confidence > 0.5:  # Lower threshold for state monitoring
                    skill.update_state(result.state, result.confidence)
                    states[skill_name] = result.state
                    
            except Exception as e:
                self.logger.error(f"State monitoring failed for {skill_name}: {e}")
                states[skill_name] = SkillState.UNKNOWN
        
        return states
    
    def _create_failed_result(self, skill: VisualSkill, region: Tuple[int, int, int, int],
                            start_time: float) -> DetectionResult:
        """Create a failed detection result"""
        return DetectionResult(
            position=SkillPosition(0, region),
            detected_skill=None,
            state=SkillState.UNKNOWN,
            confidence=0.0,
            detection_time=time.time() - start_time,
            method_used=DetectionMethod.TEMPLATE_MATCH
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_detection_time = (
            sum(self._detection_times) / len(self._detection_times)
            if self._detection_times else 0.0
        )
        
        total_cache_requests = self._cache_hits + self._cache_misses
        cache_hit_rate = (
            self._cache_hits / total_cache_requests
            if total_cache_requests > 0 else 0.0
        )
        
        return {
            "avg_detection_time_ms": avg_detection_time * 1000,
            "cache_hit_rate": cache_hit_rate,
            "templates_cached": len(self._template_cache),
            "total_detections": len(self._detection_times)
        }
    
    def clear_cache(self):
        """Clear detection caches"""
        self._template_cache.clear()
        self._position_cache.clear()
        self._detection_cache.clear()
        self._last_screenshot = None
        self.logger.info("Detection cache cleared")
    
    def optimize_detection_settings(self, results: List[DetectionResult]) -> DetectionConfig:
        """Optimize detection settings based on recent results"""
        if not results:
            return self.default_config
        
        # Analyze success rates by confidence threshold
        confidences = [r.confidence for r in results if r.detected_skill is not None]
        
        if confidences:
            # Set threshold to 95th percentile of successful detections
            new_threshold = max(0.6, np.percentile(confidences, 5))
            
            optimized_config = DetectionConfig(
                template_threshold=new_threshold,
                cooldown_threshold=self.default_config.cooldown_threshold,
                scan_interval=self.default_config.scan_interval,
                use_multi_scale=True,
                scale_range=self.default_config.scale_range
            )
            
            self.logger.info(f"Optimized detection threshold to {new_threshold:.2f}")
            return optimized_config
        
        return self.default_config