# Requirements Document

## Introduction

The Simple Entry Form Fix addresses the critical issue where the current Entry Page system gets stuck in an infinite loading state instead of displaying the expected 29 input fields directly. This system should provide immediate access to all profile data entry fields without complex dynamic loading, matching the user's expectation of seeing input fields right away as shown in the provided mockup.

## Glossary

- **Simple_Entry_Form**: Direct form interface displaying all 29 CSV fields immediately without dynamic loading
- **Static_Field_Display**: All form fields rendered directly in HTML without JavaScript-dependent schema loading
- **Immediate_Preview**: Live preview table that updates as users type, showing all 29 CSV columns
- **Direct_Field_Mapping**: One-to-one mapping between form inputs and CSV columns without complex attribute hierarchy
- **Fast_Loading**: Page loads and displays all fields within 2 seconds without loading spinners
- **CSV_Column_Structure**: Exact 29-column structure from the profile table example CSV file
- **Conditional_Display**: Smart showing/hiding of fields based on user selections (simplified version)

## Requirements

### Requirement 1

**User Story:** As a product data entry specialist, I want to see all 29 input fields immediately when I open the Profile page, so that I can start entering data without waiting for loading processes.

#### Acceptance Criteria

1. WHEN I navigate to the Profile page, THE Simple_Entry_Form SHALL display all 29 input fields within 2 seconds
2. WHEN the page loads, THE Simple_Entry_Form SHALL show field labels matching the exact CSV column names
3. WHEN I view the form, THE Simple_Entry_Form SHALL organize fields in logical sections for easy navigation
4. WHEN the form renders, THE Simple_Entry_Form SHALL not show any loading spinners or "Loading form schema..." messages
5. WHEN I access the page, THE Simple_Entry_Form SHALL display fields even if JavaScript fails to load

### Requirement 2

**User Story:** As a product data entry specialist, I want the preview table to show all 29 columns immediately and update as I type, so that I can see my data in the expected CSV format in real-time.

#### Acceptance Criteria

1. WHEN the page loads, THE Simple_Entry_Form SHALL display a preview table with all 29 CSV column headers
2. WHEN I type in any input field, THE Simple_Entry_Form SHALL update the corresponding preview column immediately
3. WHEN fields are empty, THE Simple_Entry_Form SHALL display "N/A" in the preview table
4. WHEN I enter data, THE Simple_Entry_Form SHALL format values appropriately (numbers, percentages, yes/no for booleans)
5. WHEN the preview updates, THE Simple_Entry_Form SHALL highlight changed values briefly to show the update

### Requirement 3

**User Story:** As a product data entry specialist, I want smart field visibility that shows/hides relevant fields based on my selections, so that I only see applicable options without complexity.

#### Acceptance Criteria

1. WHEN I select "Frame" as Type, THE Simple_Entry_Form SHALL show renovation-related fields
2. WHEN I check "Builtin Flyscreen Track", THE Simple_Entry_Form SHALL show flyscreen width and height fields
3. WHEN I select "Flying mullion" as Type, THE Simple_Entry_Form SHALL show clearance fields
4. WHEN I select reinforcement steel options, THE Simple_Entry_Form SHALL show steel thickness field
5. WHEN fields become hidden, THE Simple_Entry_Form SHALL clear their values and remove them from preview

### Requirement 4

**User Story:** As a product data entry specialist, I want appropriate input types for each field, so that I can enter data efficiently with proper validation and user experience.

#### Acceptance Criteria

1. WHEN I interact with dropdown fields, THE Simple_Entry_Form SHALL provide predefined options for Type, Company, Material, Opening System, and System Series
2. WHEN I interact with number fields, THE Simple_Entry_Form SHALL show appropriate units (mm, kg, m) and allow decimal input
3. WHEN I interact with percentage fields, THE Simple_Entry_Form SHALL show % symbol and limit values to 0-100
4. WHEN I interact with boolean fields, THE Simple_Entry_Form SHALL provide checkboxes for yes/no options
5. WHEN I interact with multi-select fields, THE Simple_Entry_Form SHALL allow multiple selections for Reinforcement Steel and Colours

### Requirement 5

**User Story:** As a product data entry specialist, I want to save my entered data and have it persist properly, so that I can create valid product configurations without data loss.

#### Acceptance Criteria

1. WHEN I click Save, THE Simple_Entry_Form SHALL validate all required fields before submission
2. WHEN validation passes, THE Simple_Entry_Form SHALL save data to the database as a proper Configuration record
3. WHEN save is successful, THE Simple_Entry_Form SHALL show a success message and update the URL with configuration ID
4. WHEN I reload the page with a configuration ID, THE Simple_Entry_Form SHALL populate all fields with saved values
5. WHEN save fails, THE Simple_Entry_Form SHALL show specific error messages and maintain my entered data

### Requirement 6

**User Story:** As a product data entry specialist, I want the form to work reliably without complex dependencies, so that I can always access the data entry functionality regardless of system state.

#### Acceptance Criteria

1. WHEN the database has no attribute hierarchy data, THE Simple_Entry_Form SHALL still display all 29 fields using hardcoded field definitions
2. WHEN JavaScript fails to load, THE Simple_Entry_Form SHALL still show all input fields as a functional HTML form
3. WHEN the server is slow, THE Simple_Entry_Form SHALL display fields immediately and handle save operations separately
4. WHEN there are network issues, THE Simple_Entry_Form SHALL provide offline-capable form display
5. WHEN the system encounters errors, THE Simple_Entry_Form SHALL gracefully degrade while maintaining core functionality

### Requirement 7

**User Story:** As a system administrator, I want the Simple Entry Form to integrate with existing Windx systems, so that it works seamlessly with current authentication, database, and configuration management.

#### Acceptance Criteria

1. WHEN users access the form, THE Simple_Entry_Form SHALL use existing admin authentication without changes
2. WHEN saving data, THE Simple_Entry_Form SHALL create proper Configuration and ConfigurationSelection records
3. WHEN integrating with the database, THE Simple_Entry_Form SHALL use existing database connections and transaction patterns
4. WHEN handling errors, THE Simple_Entry_Form SHALL follow established Windx error handling patterns
5. WHEN displaying the form, THE Simple_Entry_Form SHALL use existing admin template structure and styling

### Requirement 8

**User Story:** As a developer, I want the Simple Entry Form implementation to be maintainable and straightforward, so that future modifications and debugging are easy to perform.

#### Acceptance Criteria

1. WHEN implementing field definitions, THE Simple_Entry_Form SHALL use simple hardcoded field arrays instead of complex schema generation
2. WHEN implementing conditional logic, THE Simple_Entry_Form SHALL use straightforward JavaScript if/else statements instead of complex evaluators
3. WHEN implementing the preview, THE Simple_Entry_Form SHALL use direct field-to-column mapping instead of dynamic transformation
4. WHEN implementing validation, THE Simple_Entry_Form SHALL use simple client-side validation with server-side backup
5. WHEN implementing save functionality, THE Simple_Entry_Form SHALL use direct field mapping to database models