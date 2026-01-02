# Profile Hierarchy - CSV Structure Analysis (CORRECTED)

## Overview
This document represents the EXACT hierarchical structure derived from `reference/profile table example data.csv`. Based on careful analysis of the actual CSV data and column headers.

---

## Exact CSV Column Analysis

### CSV Headers (29 columns total):
1. Name
2. Type  
3. Company
4. Material
5. opening system
6. system series
7. Code
8. Length of Beam m
9. Renovation only for frame
10. width
11. builtin Flyscreen track only for sliding frame
12. Total width only for frame with builtin flyscreen
13. flyscreen track height only for frame with builtin flyscreen
14. front Height mm
15. Rear heightt
16. Glazing height
17. Renovation height mm only for frame
18. Glazing undercut heigth only for glazing bead
19. Pic
20. Sash overlap only for sashs
21. flying mullion horizontal clearance
22. flying mullion vertical clearance
23. Steel material thickness only for reinforcement
24. Weight/m kg
25. Reinforcement steel
26. Colours
27. Price/m
28. Price per/beam
29. UPVC Profile Discount%

## Complete Attribute Hierarchy (ASCII Tree)

```
Window Profile Configuration
├── Basic Information
│   ├── Name (string, required)
│   │   └── Examples: ["Frame with renovation 3.8 cm", "sash", "Mullion", "Flying Mullion", "single glazing bead", etc.]
│   ├── Type (selection, required)
│   │   ├── Frame
│   │   ├── sash
│   │   ├── Mullion  
│   │   ├── Flying mullion
│   │   ├── glazing bead
│   │   ├── Interlock
│   │   ├── Track
│   │   ├── auxilary
│   │   └── coupling, tube (from bottom rows)
│   ├── Company (selection)
│   │   └── Options: [kompen, "choose from database"]
│   ├── Material (selection, required)
│   │   └── Options: [UPVC, "Choose"]
│   ├── Opening System (selection, required)
│   │   ├── Casement (most common)
│   │   └── All (for auxiliary)
│   ├── System Series (selection, required)
│   │   ├── Kom700 (for Casement frames/sash/mullions)
│   │   ├── Kom701 (for glazing bead)
│   │   ├── Kom800 (for sliding components)
│   │   └── All (for auxiliary)
│   └── Code (string)
│       └── Examples: [705, Kom702, Kom703, xxx, Kom821, Kom811, Kom804, Kom813, Kom820, Kom421, empty]
│
├── Dimensions & Measurements
│   ├── Length of Beam (number, unit: meters)
│   │   └── Value: 6 (consistent across all rows)
│   ├── Width (number, unit: mm)
│   │   ├── Frame: [61, 71]
│   │   ├── Sash: [61, 47, 25]
│   │   ├── Mullion: [61]
│   │   ├── Flying Mullion: [n.a]
│   │   ├── Glazing Bead: [n.a]
│   │   ├── Interlock: [49]
│   │   ├── Track: [11]
│   │   └── Auxiliary: [90]
│   ├── Front Height (number, unit: mm)
│   │   ├── Frame: [31, 47]
│   │   ├── Sash: [62, 60, 37]
│   │   ├── Mullion: [42]
│   │   ├── Flying Mullion: [empty]
│   │   ├── Glazing Bead: [26]
│   │   ├── Interlock: [n.a]
│   │   ├── Track: [8.5]
│   │   └── Auxiliary: [60]
│   ├── Rear Height (number, unit: mm)
│   │   ├── Frame: [51, n.a]
│   │   ├── Sash: [62, 78, 49]
│   │   ├── Mullion: [82]
│   │   ├── All others: [n.a or empty]
│   ├── Glazing Height (number, unit: mm)
│   │   ├── Frame: [20]
│   │   ├── Sash: [20, 18, 12]
│   │   ├── Mullion: [20]
│   │   └── All others: [n.a or empty]
│   └── Weight per Meter (number, unit: kg)
│       ├── Frame: [1045]
│       ├── Sash: [1250]
│       ├── Mullion: [1.17]
│       └── All others: [empty]
│
├── Renovation Options (Frame Only)
│   ├── Renovation (selection)
│   │   ├── Display Condition: Type = "Frame"
│   │   ├── Options: [yes/no, yes, no, n.a]
│   │   └── Column: "Renovation only for frame"
│   └── Renovation Height (number, unit: mm)
│       ├── Display Condition: Type = "Frame"
│       ├── Values: [38, 40, 0]
│       └── Column: "Renovation height mm only for frame"
│
├── Flyscreen Configuration (Sliding Frame Only)
│   ├── Builtin Flyscreen Track (selection)
│   │   ├── Display Condition: "sliding frame" in Name OR System Series = "Kom800"
│   │   ├── Options: [n.a, yes]
│   │   └── Column: "builtin Flyscreen track only for sliding frame"
│   ├── Total Width (number, unit: mm)
│   │   ├── Display Condition: Builtin Flyscreen Track = "yes"
│   │   ├── Values: [n.a, 108]
│   │   └── Column: "Total width only for frame with builtin flyscreen"
│   └── Flyscreen Track Height (number, unit: mm)
│       ├── Display Condition: Builtin Flyscreen Track = "yes"
│       ├── Values: [n.a, 37.5]
│       └── Column: "flyscreen track height only for frame with builtin flyscreen"
│
├── Glazing Specifications
│   ├── Glazing Undercut Height (number, unit: mm)
│   │   ├── Display Condition: Type = "glazing bead"
│   │   ├── Values: [n.a, 3]
│   │   └── Column: "Glazing undercut heigth only for glazing bead"
│   └── Pic (string, optional)
│       └── All values are empty in CSV
│
├── Sash & Mullion Details
│   ├── Sash Overlap (number, unit: mm)
│   │   ├── Display Condition: Type = "sash"
│   │   ├── Values: [n.a, 8]
│   │   └── Column: "Sash overlap only for sashs"
│   ├── Flying Mullion Horizontal Clearance (number, unit: mm)
│   │   ├── Display Condition: Type = "Flying mullion"
│   │   ├── Values: [n.a, 6]
│   │   └── Column: "flying mullion horizontal clearance"
│   └── Flying Mullion Vertical Clearance (number, unit: mm)
│       ├── Display Condition: Type = "Flying mullion"
│       ├── Values: [n.a, 40]
│       └── Column: "flying mullion vertical clearance"
│
├── Reinforcement & Materials
│   ├── Steel Material Thickness (number, unit: mm)
│   │   ├── Display Condition: When Reinforcement Steel is selected
│   │   ├── Values: [n.a, empty]
│   │   └── Column: "Steel material thickness only for reinforcement"
│   └── Reinforcement Steel (multi-selection)
│       ├── Values: ["multi choice from steel database", empty]
│       └── Column: "Reinforcement steel"
│
├── Appearance & Finishing
│   ├── Colours (multi-selection)
│   │   ├── Values: ["White", "whit, nussbaum", empty]
│   │   └── Note: "write multiple according to colour" from instruction row
│   └── UPVC Profile Discount (percentage)
│       ├── Value: 20% (consistent across all rows)
│       └── Column: "UPVC Profile Discount%"
│
└── Pricing Information
    ├── Price per Meter (currency)
    │   ├── Values: [150, 200,500, empty]
    │   └── Column: "Price/m"
    └── Price per Beam (currency)
        ├── Values: [900, empty]
        └── Column: "Price per/beam"
```

---

## Conditional Logic Rules (Based on Actual CSV Data)

### Primary Conditions from Column Headers
```
1. Renovation Fields (Frame Only)
   Column: "Renovation only for frame"
   Column: "Renovation height mm only for frame"
   IF Type = "Frame" THEN show these fields

2. Flyscreen Fields (Sliding Frame Only)  
   Column: "builtin Flyscreen track only for sliding frame"
   Column: "Total width only for frame with builtin flyscreen"
   Column: "flyscreen track height only for frame with builtin flyscreen"
   IF Type contains "sliding" OR System Series = "Kom800" THEN show flyscreen track
   IF Flyscreen Track = "yes" THEN show total width and track height

3. Type-Specific Fields
   Column: "Sash overlap only for sashs"
   IF Type = "sash" THEN show sash overlap
   
   Columns: "flying mullion horizontal clearance", "flying mullion vertical clearance"
   IF Type = "Flying mullion" THEN show clearance fields
   
   Column: "Glazing undercut heigth only for glazing bead"
   IF Type = "glazing bead" THEN show undercut height

4. Reinforcement Fields
   Column: "Steel material thickness only for reinforcement"
   IF "Reinforcement steel" is selected THEN show steel thickness
```

### Actual Field Visibility Matrix (From CSV Data)
```
Field Name                          | Frame | sash | Mullion | Flying | glazing | Interlock | Track | auxilary
                                   |       |      |         | mullion| bead    |           |       |
-----------------------------------|-------|------|---------|--------|---------|-----------|-------|----------
Name                               |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Type                               |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Company                            |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Material                           |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Opening System                     |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
System Series                      |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Code                               |   ✓   |  ✓   |    ✓    |   ✓    |    ✗    |     ✓     |   ✓   |    ✓
Length of Beam                     |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Renovation                         |   ✓   |  ✗   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Width                              |   ✓   |  ✓   |    ✓    |   ✗    |    ✗    |     ✓     |   ✓   |    ✓
Flyscreen Track                    |   S   |  S   |    S    |   S    |    S    |     S     |   S   |    S
Flyscreen Total Width              |   F   |  F   |    F    |   F    |    F    |     F     |   F   |    F
Flyscreen Track Height             |   F   |  F   |    F    |   F    |    F    |     F     |   F   |    F
Front Height                       |   ✓   |  ✓   |    ✓    |   ✗    |    ✓    |     ✗     |   ✓   |    ✓
Rear Height                        |   ✓   |  ✓   |    ✓    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Glazing Height                     |   ✓   |  ✓   |    ✓    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Renovation Height                  |   ✓   |  ✗   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Glazing Undercut Height            |   ✗   |  ✗   |    ✗    |   ✗    |    ✓    |     ✗     |   ✗   |    ✗
Pic                                |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓
Sash Overlap                       |   ✗   |  ✓   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Flying Mullion H Clearance         |   ✗   |  ✗   |    ✗    |   ✓    |    ✗    |     ✗     |   ✗   |    ✗
Flying Mullion V Clearance         |   ✗   |  ✗   |    ✗    |   ✓    |    ✗    |     ✗     |   ✗   |    ✗
Steel Thickness                    |   R   |  R   |    R    |   R    |    R    |     R     |   R   |    R
Weight/m                           |   ✓   |  ✓   |    ✓    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Reinforcement Steel                |   ✓   |  ✓   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Colours                            |   ✓   |  ✓   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Price/m                            |   ✓   |  ✓   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
Price per Beam                     |   ✓   |  ✗   |    ✗    |   ✗    |    ✗    |     ✗     |   ✗   |    ✗
UPVC Profile Discount              |   ✓   |  ✓   |    ✓    |   ✓    |    ✓    |     ✓     |   ✓   |    ✓

Legend:
✓ = Has data in CSV (always visible)
✗ = Always n.a or empty (never visible)
S = Visible only for sliding frames (System Series = Kom800)
F = Visible only when Flyscreen Track = "yes"
R = Visible only when Reinforcement Steel is selected
```

---

## Data Types & Validation Rules

### Input Field Types
```
string          → Text input (Name, Code, Pic)
selection       → Dropdown/Select (Type, Material, Opening System)
multi-selection → Multi-select dropdown (Colors, Reinforcement Steel)
number          → Numeric input (Width, Height, Weight, Price)
boolean         → Checkbox/Toggle (Renovation, Builtin Flyscreen Track)
percentage      → Numeric input with % symbol (UPVC Profile Discount)
currency        → Numeric input with currency symbol (Price fields)
```

### Validation Rules
```javascript
// Example validation rules for key fields
{
  "name": {
    "required": true,
    "maxLength": 100,
    "pattern": "^[a-zA-Z0-9\\s\\-_]+$"
  },
  "width": {
    "type": "number",
    "min": 1,
    "max": 5000,
    "unit": "mm"
  },
  "length_of_beam": {
    "type": "number", 
    "min": 0.1,
    "max": 50,
    "unit": "meters",
    "step": 0.1
  },
  "upvc_profile_discount": {
    "type": "percentage",
    "min": 0,
    "max": 100,
    "default": 20
  }
}
```

---

## Implementation Notes

### Database Schema Mapping
```python
# Each CSV column maps to an AttributeNode
manufacturing_type_id = window_profile_type.id

# Basic Information nodes
name_node = AttributeNode(
    name="Name",
    node_type="attribute", 
    data_type="string",
    required=True,
    ltree_path="basic_info.name"
)

type_node = AttributeNode(
    name="Type",
    node_type="attribute",
    data_type="selection", 
    required=True,
    ltree_path="basic_info.type"
)

# Conditional nodes
renovation_height_node = AttributeNode(
    name="Renovation Height",
    node_type="attribute",
    data_type="number",
    display_condition={
        "operator": "and",
        "conditions": [
            {"field": "type", "operator": "equals", "value": "Frame"},
            {"field": "renovation", "operator": "equals", "value": true}
        ]
    },
    ltree_path="renovation.renovation_height"
)
```

### Form Generation Logic
```javascript
// Dynamic form field generation
function generateFormField(attributeNode) {
    const field = {
        name: attributeNode.name,
        type: attributeNode.data_type,
        required: attributeNode.required,
        visible: evaluateDisplayCondition(attributeNode.display_condition),
        validation: attributeNode.validation_rules
    };
    
    return createInputElement(field);
}
```

### Preview Table Mapping
```javascript
// Map form data to CSV table structure
function generatePreviewRow(formData) {
    return {
        "Name": formData.name || "N/A",
        "Type": formData.type || "N/A", 
        "Width": formData.width || "N/A",
        "Builtin Flyscreen Track": formData.builtin_flyscreen_track || "N/A",
        // ... map all 27 columns
    };
}
```

---

## Summary

This hierarchy represents **27 distinct data fields** organized into **8 logical categories** with **4 primary conditional logic rules**. The structure supports:

- ✅ Dynamic form generation based on Type and Opening System selections
- ✅ Conditional field visibility with complex AND/OR logic
- ✅ Multi-level validation (client-side and server-side)
- ✅ Real-time preview table matching exact CSV structure
- ✅ Extensible design for future field additions

The hierarchy is designed to be implemented using the existing Windx `AttributeNode` system with LTREE paths for efficient querying and `display_condition` JSONB fields for conditional logic.