# Implementation Plan

- [-] 1. Fix critical JavaScript bugs

  - Fix syntax error in renderField() function at line 741
  - Add missing showToast() function for error handling
  - Test that schema loading works and fields render
  - _Requirements: 1.1, 1.4, 6.2_

- [ ] 2. Implement tabbed interface layout
  - Replace dual-view container with tabbed interface HTML structure
  - Add tab buttons for "Input" and "Preview" tabs
  - Implement tab switching JavaScript functionality
  - Update CSS to support tabbed layout instead of dual-view
  - _Requirements: 1.1, 2.1, 8.2_

- [ ] 3. Redesign input field layout
  - Convert complex sectioned form to simple vertical field list
  - Style fields as clean vertical stack matching wireframe
  - Ensure all 29 fields display immediately without loading
  - Keep existing conditional field visibility logic
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Update preview tab functionality
  - Move preview table to separate tab instead of side-by-side view
  - Ensure preview updates when switching to preview tab
  - Keep all 29 CSV column headers and real-time updates
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5. Test and verify functionality
  - Verify page loads all 29 fields within 2 seconds
  - Test tab switching between Input and Preview
  - Test conditional field visibility (Frame type, flyscreen, etc.)
  - Test save functionality creates proper Configuration records
  - Test form works even if JavaScript partially fails
  - _Requirements: 1.1, 1.4, 1.5, 5.1, 5.2, 5.3, 6.1, 6.2_

- [ ] 6. Checkpoint - Ensure all functionality works
  - Ensure all tests pass, ask the user if questions arise.