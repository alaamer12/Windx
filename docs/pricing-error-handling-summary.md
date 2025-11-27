# Pricing Service Error Handling Implementation

## Overview

Task 9.2 has been completed: comprehensive error handling has been added to all price calculation methods in the PricingService.

## Implementation Details

### 1. Formula Evaluation Error Handling (`evaluate_price_formula`)

The `evaluate_price_formula` method now handles:

- **Division by Zero**: Explicitly caught and reported with meaningful error messages
  ```python
  except ZeroDivisionError:
      raise InvalidFormulaException(
          message="Division by zero in formula",
          formula=formula,
          details={
              "error": "Division by zero",
              "error_type": "division_by_zero",
              "context": context,
          },
      )
  ```

- **Unknown Variables**: Caught when variables are not in the context
  ```python
  except KeyError as e:
      raise InvalidFormulaException(
          message=f"Unknown variable in formula: {str(e)}",
          formula=formula,
          details={
              "error": str(e),
              "error_type": "unknown_variable",
              "available_variables": list(context.keys()),
          },
      )
  ```

- **Calculation Errors**: Handles overflow, underflow, and invalid operations
  ```python
  except (ValueError, OverflowError) as e:
      raise InvalidFormulaException(
          message=f"Calculation error in formula: {str(e)}",
          formula=formula,
          details={
              "error": str(e),
              "error_type": "calculation_error",
              "context": context,
          },
      )
  ```

- **Syntax Errors**: Catches invalid formula syntax
  ```python
  except SyntaxError as e:
      raise InvalidFormulaException(
          message=f"Formula syntax error: {str(e)}",
          formula=formula,
          details={"error": str(e), "error_type": "syntax_error"},
      )
  ```

- **Invalid Results**: Validates results are finite and within reasonable range
  ```python
  if not isinstance(result, (int, float)) or not (-1e10 < result < 1e10):
      raise InvalidFormulaException(
          message="Formula result is invalid or out of range",
          formula=formula,
          details={
              "result": str(result),
              "error_type": "invalid_result",
          },
      )
  ```

- **Unexpected Errors**: Catch-all for any other exceptions
  ```python
  except Exception as e:
      raise InvalidFormulaException(
          message=f"Unexpected error evaluating formula: {str(e)}",
          formula=formula,
          details={
              "error": str(e),
              "error_type": "unexpected_error",
              "exception_type": type(e).__name__,
          },
      )
  ```

### 2. Selection Impact Calculation Error Handling (`calculate_selection_impact`)

The `calculate_selection_impact` method wraps formula evaluation and adds context:

- **Price Formula Errors**: Re-raises with attribute node context
  ```python
  except InvalidFormulaException as e:
      raise InvalidFormulaException(
          message=f"Error calculating price impact for attribute node {attr_node.id}: {e.message}",
          formula=attr_node.price_formula,
          details={
              **e.details,
              "attribute_node_id": attr_node.id,
              "attribute_node_name": attr_node.name,
              "selection_id": selection.id,
          },
      )
  ```

- **Weight Formula Errors**: Similar handling for weight calculations

### 3. Configuration Price Calculation Error Handling (`calculate_configuration_price`)

The `calculate_configuration_price` method now handles errors for each selection:

- **Formula Errors**: Re-raises with configuration context
  ```python
  except InvalidFormulaException as e:
      raise InvalidFormulaException(
          message=f"Error calculating price for configuration {config_id}: {e.message}",
          formula=e.details.get("formula"),
          details={
              **e.details,
              "configuration_id": config_id,
              "selection_id": selection.id,
          },
      )
  ```

- **Unexpected Errors**: Catches any other errors during calculation
  ```python
  except Exception as e:
      raise InvalidFormulaException(
          message=f"Unexpected error calculating price for configuration {config_id}: {str(e)}",
          details={
              "configuration_id": config_id,
              "selection_id": selection.id,
              "error": str(e),
              "error_type": type(e).__name__,
          },
      )
  ```

### 4. AST Node Evaluation Error Handling (`_eval_node`)

The `_eval_node` method includes:

- **Range Validation**: Checks values are within acceptable range
  ```python
  if not (-1e10 < value < 1e10):
      raise ValueError(f"Constant value out of range: {value}")
  ```

- **Division by Zero**: Special handling for division operations
  ```python
  if isinstance(node.op, ast.Div):
      if right == 0:
          raise ZeroDivisionError("Division by zero")
  ```

- **Result Validation**: Ensures operation results are valid
  ```python
  if not isinstance(result, (int, float)) or not (-1e10 < result < 1e10):
      raise ValueError(f"Operation result out of range: {result}")
  ```

## Error Message Quality

All error messages include:

1. **Clear Description**: What went wrong
2. **Formula Context**: The formula that caused the error
3. **Error Type**: Categorized error type for programmatic handling
4. **Relevant Details**: Context-specific information (variable values, node IDs, etc.)
5. **Available Variables**: For unknown variable errors, shows what variables are available

## Example Error Response

```json
{
  "error": "invalid_formula_error",
  "message": "Error calculating price for configuration 123: Division by zero in formula",
  "details": {
    "formula": "width / height",
    "error": "Division by zero",
    "error_type": "division_by_zero",
    "context": {"width": 100, "height": 0},
    "configuration_id": 123,
    "selection_id": 456,
    "attribute_node_id": 789,
    "attribute_node_name": "Window Dimensions"
  }
}
```

## Benefits

1. **Debugging**: Detailed error information helps developers identify issues quickly
2. **User Experience**: Meaningful error messages can be shown to users
3. **Monitoring**: Error types enable tracking of common issues
4. **Security**: Safe formula evaluation prevents code injection
5. **Reliability**: Graceful handling prevents system crashes

## Testing

Comprehensive unit tests have been created in `tests/unit/services/test_pricing_error_handling.py` covering:

- Division by zero (constant and variable)
- Unknown variables
- Syntax errors
- Overflow/underflow
- Invalid results
- Empty formulas
- Error context propagation
- Meaningful error messages

Note: Tests require PostgreSQL for JSONB support. SQLite-based tests will fail due to JSONB incompatibility.

## Requirements Satisfied

✅ **Requirement 12.4**: Error handling for price calculations
- Wrap formula evaluation in try/except ✓
- Handle division by zero and invalid operations ✓
- Return meaningful error messages ✓
- Add to PricingService methods ✓

## Related Files

- `app/services/pricing.py` - Main implementation
- `app/core/exceptions.py` - Exception definitions
- `tests/unit/services/test_pricing_error_handling.py` - Test suite
- `docs/pricing-error-handling-summary.md` - This document
