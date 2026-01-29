# Configuration Files

This directory contains YAML configuration files for the WindX hierarchy setup system.

## Overview

The WindX system uses YAML configuration files to define manufacturing types and their attribute hierarchies. This approach replaces the previous hardcoded Python setup scripts with a flexible, maintainable configuration system.

## Directory Structure

```
backend/config/
├── pages/                    # Page-specific configurations
│   ├── profile.yaml         # Profile page attributes (29 fields)
│   ├── accessories.yaml     # Accessories page attributes
│   └── glazing.yaml         # Glazing page attributes
└── README.md               # This documentation
```

## YAML File Structure

Each YAML configuration file follows this structure:

```yaml
# Page identification
page_type: profile                    # Unique page identifier
manufacturing_type: Window Profile Entry  # Manufacturing type name

# Manufacturing type configuration
manufacturing_type_config:
  description: "Description of the manufacturing type"
  base_category: window
  base_price: 200.00
  base_weight: 15.00

# Attribute definitions
attributes:
  - name: attribute_name              # Required: unique attribute name
    display_name: Display Name        # Optional: human-readable name
    description: |                    # Optional: rich description with examples
      Multi-line description with examples and guidance.
      
      **Examples:**
      • Example 1
      • Example 2
    node_type: attribute              # Required: attribute, category, option
    data_type: string                 # Required: string, number, boolean
    required: true                    # Required: true/false
    ltree_path: section.attribute     # Optional: hierarchical path
    depth: 1                          # Optional: tree depth level
    sort_order: 1                     # Optional: display order
    ui_component: input               # Required: input, dropdown, checkbox, etc.
    help_text: Brief help text        # Optional: tooltip text
    validation_rules:                 # Optional: validation constraints
      min_length: 1
      max_length: 200
      options:                        # For dropdown/select components
        - Option 1
        - Option 2
    display_condition:                # Optional: conditional display logic
      operator: equals
      field: other_field
      value: some_value
    calculated_field:                 # Optional: calculated field definition
      type: multiply
      operands: [field1, field2]
      trigger_on: [field1]
      precision: 2
    metadata:                         # Optional: additional metadata
      placeholder: "e.g. Example value"
```

## Field Types and Components

### Data Types
- `string` - Text values
- `number` - Numeric values (integer or decimal)
- `boolean` - True/false values

### UI Components
- `input` - Text input field
- `number` - Numeric input field
- `dropdown` - Select from predefined options
- `checkbox` - Boolean checkbox
- `currency` - Currency input with formatting
- `percentage` - Percentage input
- `file` - File upload
- `text` - Multi-line text area
- `multi-select` - Multiple selection from options

### Node Types
- `attribute` - Configurable property
- `category` - Organizational grouping
- `option` - Specific choice for an attribute

## Validation Rules

### String Validation
```yaml
validation_rules:
  min_length: 1
  max_length: 200
  pattern: "^[A-Z]{2}\\d{5}$"
  message: "Custom validation message"
```

### Number Validation
```yaml
validation_rules:
  min: 0
  max: 100
```

### Options (Dropdown/Select)
```yaml
validation_rules:
  options:
    - Option 1
    - Option 2
    - Option 3
```

## Display Conditions

Control when attributes are shown based on other field values:

### Simple Condition
```yaml
display_condition:
  operator: equals
  field: material_type
  value: Wood
```

### Complex Conditions
```yaml
display_condition:
  operator: and
  conditions:
    - operator: equals
      field: type
      value: Frame
    - operator: contains
      field: opening_system
      value: sliding
```

### Available Operators
- `equals` - Field equals specific value
- `not_equals` - Field does not equal value
- `contains` - Field contains substring
- `in` - Field value is in list
- `gt` / `lt` - Greater than / less than (numbers)
- `exists` - Field has any value
- `is_not_empty` - Field is not null/empty
- `and` / `or` - Combine multiple conditions

## Calculated Fields

Define fields that are automatically calculated from other fields:

```yaml
calculated_field:
  type: divide                        # Calculation type
  operands: [price_per_beam, length_of_beam]  # Input fields
  trigger_on: [price_per_beam]        # Fields that trigger recalculation
  precision: 2                        # Decimal places
```

### Calculation Types
- `multiply` - Multiply operands
- `divide` - Divide first by second operand
- `add` - Add operands
- `subtract` - Subtract second from first operand

## Usage

### Setup All Pages
```bash
python scripts/setup_hierarchy.py
```

### Setup Specific Page
```bash
python scripts/setup_hierarchy.py profile
python scripts/setup_hierarchy.py accessories
python scripts/setup_hierarchy.py glazing
```

### Validate YAML Syntax
```bash
python -c "import yaml; yaml.safe_load(open('backend/config/pages/profile.yaml'))"
```

## Adding New Pages

1. Create new YAML file in `backend/config/pages/`
2. Follow the structure documented above
3. Run setup script: `python scripts/setup_hierarchy.py your_page_name`

## Best Practices

### Naming Conventions
- Use snake_case for attribute names
- Use descriptive display names
- Keep ltree_path hierarchical and logical

### Descriptions
- Provide rich descriptions with examples
- Use markdown formatting for better readability
- Include business context and usage guidance

### Validation
- Always validate YAML syntax before deployment
- Test display conditions thoroughly
- Verify calculated fields work correctly

### Organization
- Group related attributes logically
- Use consistent sort_order values
- Maintain depth hierarchy properly

## Troubleshooting

### YAML Syntax Errors
- Check indentation (use spaces, not tabs)
- Verify quotes around special characters
- Ensure proper list formatting

### Display Conditions Not Working
- Verify field names match exactly
- Check operator spelling
- Test conditions with simple cases first

### Calculated Fields Not Updating
- Ensure trigger_on fields are correct
- Verify operand field names exist
- Check calculation type is supported

## Migration from Old Scripts

The YAML configuration system replaces the old hardcoded Python setup scripts:
- `setup_profile_hierarchy.py` → `profile.yaml`
- `setup_accessories_hierarchy.py` → `accessories.yaml`
- `setup_glazing_hierarchy.py` → `glazing.yaml`

All functionality has been preserved while making the system more maintainable and flexible.