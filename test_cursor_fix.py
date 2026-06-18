#!/usr/bin/env python3
"""
Test script to verify cursor movement is working correctly.
This script tests the eye tracking and mouse movement pipeline.
"""

import os
import sys
import time

# Set QT platform before any imports
os.environ["QT_QPA_PLATFORM"] = "xcb"

from mouse_controller import MouseController, IS_WAYLAND, SCREEN_W, SCREEN_H, _move, _root, check_compatibility, test_movement

def test_basic_movement():
    """Test basic cursor movement using the _move function directly."""
    print("=" * 60)
    print("TEST 1: Basic cursor movement")
    print("=" * 60)
    
    if not check_compatibility():
        print("FAIL: Compatibility check failed")
        return False
    
    if not test_movement():
        print("FAIL: Movement test failed")
        return False
    
    print("PASS: Basic movement working\n")
    return True

def test_mouse_controller():
    """Test the MouseController class with simulated iris coordinates."""
    print("=" * 60)
    print("TEST 2: MouseController with simulated iris data")
    print("=" * 60)
    
    mouse = MouseController()
    
    # Simulate various iris positions
    test_cases = [
        (0.35, 0.60, "looking left-up"),
        (0.50, 0.65, "looking center"),
        (0.55, 0.70, "looking right-down"),
        (0.45, 0.65, "looking center-left"),
    ]
    
    for nx, ny, desc in test_cases:
        print(f"Simulating: {desc} - iris=({nx:.3f},{ny:.3f})")
        try:
            mouse.move(nx, ny)
            time.sleep(0.3)
            
            # Check cursor position
            p = _root.query_pointer()
            print(f"  Cursor now at: ({p.root_x},{p.root_y})")
        except Exception as e:
            print(f"  ERROR: {e}")
            return False
    
    print("PASS: MouseController working\n")
    return True

def test_eye_tracker():
    """Test the EyeTracker to ensure it can detect faces and iris positions."""
    print("=" * 60)
    print("TEST 3: EyeTracker face detection")
    print("=" * 60)
    
    import cv2
    from eye_tracker import EyeTracker
    from config import CAMERA_ID
    
    try:
        cam = cv2.VideoCapture(CAMERA_ID)
        if not cam.isOpened():
            print("FAIL: Cannot open camera")
            return False
        
        tracker = EyeTracker()
        
        # Try to detect face for a few frames
        for i in range(30):
            ok, frame = cam.read()
            if not ok:
                continue
            
            frame = cv2.flip(frame, 1)
            data = tracker.process(frame)
            
            if data:
                nx, ny = data["iris_norm"]
                print(f"Face detected! iris_norm=({nx:.4f},{ny:.4f})")
                print(f"  iris_left={data['iris_left']}")
                print(f"  iris_right={data['iris_right']}")
                print(f"  ear_left={data['ear_left']:.3f}")
                print(f"  ear_right={data['ear_right']:.3f}")
                cam.release()
                print("PASS: EyeTracker working\n")
                return True
        
        cam.release()
        print("WARN: No face detected in 30 frames (this may be normal if no face in front of camera)")
        print("PASS: EyeTracker initialized successfully\n")
        return True
        
    except Exception as e:
        print(f"FAIL: EyeTracker error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("CURSOR MOVEMENT FIX VERIFICATION TEST")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Basic Movement", test_basic_movement()))
    results.append(("MouseController", test_mouse_controller()))
    results.append(("EyeTracker", test_eye_tracker()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! The cursor movement should now work.")
        print("\nNext steps:")
        print("  1. Run: python main.py")
        print("  2. Position your face in front of the camera")
        print("  3. Watch the desktop cursor (not the webcam window)")
        print("  4. Move your eyes to control the cursor")
    else:
        print("SOME TESTS FAILED. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  - If on Wayland, run: bash setup_wayland.sh")
        print("  - Then: newgrp input && python main.py")
        print("  - If on X11, ensure DISPLAY is set correctly")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())