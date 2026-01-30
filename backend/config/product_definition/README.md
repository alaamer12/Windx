# Product Definition Configuration

This directory contains YAML configuration files that define product definition scopes, entities, and their metadata. These configurations replace the hard-coded `DEFINITION_SCOPES` constant in the relations service.

## Structure

Each YAML file defines a complete scope with:

- **scope**: Unique identifier for the scope
- **label**: Human-readable name for the scope
- **description**: Description of what this scope manages
- **entities**: Dictionary of entity types and their configurations
- **hierarchy**: Mapping of hierarchy levels to entity types
- **dependencies**: Auto-fill dependencies between fields

## Entity Configuration

Each entity can have:

```yaml
entity_name:
  label: "Human Readable Name"
  icon: "pi pi-icon-name"  # PrimeVue icon
  placeholders:
    name: "Placeholder for name field"
    description: "Placeholder for description field"
    price: "Placeholder for price field"
  metadata_fields:
    - name: field_name
      type: text|number|boolean|textarea
      label: "Field Label"
      placeholder: "Field placeholder"
      hidden: true  # Optional, hides field from UI
  special_ui:  # Optional special UI configuration
    type: relation_selector
    config:
      field_name: linked_field_name
      target_entity: target_entity_type
      label: "UI Label"
      required: true
      help_text: "Help text for users"
```

## Setup

After modifying configuration files, run the setup script:

```bash
# Setup all scopes
python backend/scripts/setup_product_definitions.py

# Setup specific scope
python backend/scripts/setup_product_definitions.py profile
```

## Available Scopes

- **profile**: Window and door profile definitions
- **glazing**: Glass unit, spacer, and gas filling definitions  
- **hardware**: Handle, hinge, lock, and accessory definitions

## Adding New Scopes

1. Create a new YAML file in this directory
2. Define the scope configuration following the existing patterns
3. Run the setup script to load the configuration into the database
4. The new scope will be automatically available in the admin interface

## Migration from Hard-coded Constants

The system automatically loads these configurations from the database instead of the hard-coded `DEFINITION_SCOPES` constant. The relations service caches the loaded configurations for performance.

To clear the cache and reload from database:
```python
relations_service.clear_definition_scopes_cache()
```