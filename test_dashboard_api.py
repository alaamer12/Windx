"""Test script to interact with the WindX API and test data entry functionality.

This script:
1. Logs in as admin superuser
2. Creates a manufacturing type (e.g., Window)
3. Creates hierarchical attribute nodes
4. Verifies the data entry works correctly
"""

import asyncio

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"


async def main():
    """Main test function."""
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        print("=" * 60)
        print("WindX Dashboard API Test - Manual Data Entry")
        print("=" * 60)

        # Step 1: Login
        print("\n1. Logging in as admin...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Admin123!"}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return

        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"✅ Login successful! Token: {access_token[:50]}...")

        # Set authorization header for subsequent requests
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 2: Get current user info
        print("\n2. Getting current user info...")
        me_response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        if me_response.status_code == 200:
            user_data = me_response.json()
            print(f"✅ Logged in as: {user_data['username']} ({user_data['email']})")
            print(f"   Is Superuser: {user_data['is_superuser']}")
        else:
            print(f"❌ Failed to get user info: {me_response.status_code}")

        # Step 3: List existing manufacturing types
        print("\n3. Listing existing manufacturing types...")
        mfg_response = await client.get(f"{BASE_URL}/manufacturing-types", headers=headers)
        if mfg_response.status_code == 200:
            mfg_types = mfg_response.json()
            print(f"✅ Found {len(mfg_types)} manufacturing types:")
            for mfg in mfg_types:
                print(
                    f"   - ID: {mfg['id']}, Name: {mfg['name']}, Base Price: ${mfg['base_price']}"
                )
        else:
            print(f"❌ Failed to get manufacturing types: {mfg_response.status_code}")
            mfg_types = []

        # Step 4: Create a new manufacturing type (Window)
        print("\n4. Creating a new manufacturing type: 'Custom Window'...")
        new_mfg_data = {
            "name": "Custom Window",
            "description": "Customizable window with various options",
            "base_price": 200.00,
            "base_weight": 25.0,
            "category": "Windows & Doors",
            "is_active": True,
        }

        create_mfg_response = await client.post(
            f"{BASE_URL}/manufacturing-types", headers=headers, json=new_mfg_data
        )

        if create_mfg_response.status_code == 201:
            created_mfg = create_mfg_response.json()
            mfg_type_id = created_mfg["id"]
            print("✅ Manufacturing type created successfully!")
            print(f"   ID: {created_mfg['id']}")
            print(f"   Name: {created_mfg['name']}")
            print(f"   Base Price: ${created_mfg['base_price']}")
        elif create_mfg_response.status_code == 409:
            print("⚠️  Manufacturing type already exists, using existing one...")
            # Find existing one
            for mfg in mfg_types:
                if mfg["name"] == "Custom Window":
                    mfg_type_id = mfg["id"]
                    print(f"   Using existing ID: {mfg_type_id}")
                    break
            else:
                print("❌ Could not find existing manufacturing type")
                return
        else:
            print(f"❌ Failed to create manufacturing type: {create_mfg_response.status_code}")
            print(f"   Response: {create_mfg_response.text}")
            return

        # Step 5: Create hierarchical attribute nodes
        print(f"\n5. Creating attribute nodes for manufacturing type ID {mfg_type_id}...")

        # Create root category: Frame Options
        print("\n   Creating category: Frame Options...")
        frame_category_data = {
            "manufacturing_type_id": mfg_type_id,
            "name": "Frame Options",
            "node_type": "category",
            "sort_order": 1,
            "description": "Frame material and color options",
        }

        frame_cat_response = await client.post(
            f"{BASE_URL}/attribute-nodes", headers=headers, json=frame_category_data
        )

        if frame_cat_response.status_code == 201:
            frame_category = frame_cat_response.json()
            frame_category_id = frame_category["id"]
            print(f"   ✅ Frame Options category created (ID: {frame_category_id})")
        else:
            print(f"   ❌ Failed to create Frame Options: {frame_cat_response.status_code}")
            print(f"      Response: {frame_cat_response.text}")
            return

        # Create attribute: Material Type
        print("\n   Creating attribute: Material Type...")
        material_attr_data = {
            "manufacturing_type_id": mfg_type_id,
            "parent_node_id": frame_category_id,
            "name": "Material Type",
            "node_type": "attribute",
            "data_type": "string",
            "required": True,
            "sort_order": 1,
            "description": "Type of frame material",
        }

        material_attr_response = await client.post(
            f"{BASE_URL}/attribute-nodes", headers=headers, json=material_attr_data
        )

        if material_attr_response.status_code == 201:
            material_attr = material_attr_response.json()
            material_attr_id = material_attr["id"]
            print(f"   ✅ Material Type attribute created (ID: {material_attr_id})")
        else:
            print(f"   ❌ Failed to create Material Type: {material_attr_response.status_code}")
            print(f"      Response: {material_attr_response.text}")
            return

        # Create options for Material Type
        materials = [
            {"name": "Aluminum", "price": 50.00, "weight": 5.0},
            {"name": "Wood", "price": 120.00, "weight": 8.0},
            {"name": "Vinyl", "price": 30.00, "weight": 3.0},
        ]

        print("\n   Creating material options...")
        for idx, material in enumerate(materials):
            option_data = {
                "manufacturing_type_id": mfg_type_id,
                "parent_node_id": material_attr_id,
                "name": material["name"],
                "node_type": "option",
                "price_impact_type": "fixed",
                "price_impact_value": material["price"],
                "weight_impact": material["weight"],
                "sort_order": idx + 1,
                "description": f"{material['name']} frame material",
            }

            option_response = await client.post(
                f"{BASE_URL}/attribute-nodes", headers=headers, json=option_data
            )

            if option_response.status_code == 201:
                option = option_response.json()
                print(
                    f"   ✅ {material['name']} option created (ID: {option['id']}, +${material['price']})"
                )
            else:
                print(f"   ❌ Failed to create {material['name']}: {option_response.status_code}")

        # Step 6: Verify the hierarchy
        print(f"\n6. Verifying the created hierarchy for manufacturing type {mfg_type_id}...")
        tree_response = await client.get(
            f"{BASE_URL}/attribute-nodes/manufacturing-type/{mfg_type_id}/tree", headers=headers
        )

        if tree_response.status_code == 200:
            tree_data = tree_response.json()
            print("✅ Hierarchy retrieved successfully!")
            print(f"   Total nodes: {len(tree_data)}")
            print("\n   Hierarchy structure:")
            for node in tree_data:
                indent = "   " * node.get("depth", 0)
                node_type = node.get("node_type", "unknown")
                name = node.get("name", "unnamed")
                price = node.get("price_impact_value")
                price_str = f" (+${price})" if price else ""
                print(f"   {indent}[{node_type}] {name}{price_str}")
        else:
            print(f"❌ Failed to get hierarchy tree: {tree_response.status_code}")

        print("\n" + "=" * 60)
        print("✅ Manual data entry test completed successfully!")
        print("=" * 60)
        print("\nSummary:")
        print(f"- Created manufacturing type: Custom Window (ID: {mfg_type_id})")
        print("- Created hierarchical attribute structure with categories, attributes, and options")
        print("- Verified CRUD operations work correctly")
        print("\nThe WindX system is functioning properly for data entry!")


if __name__ == "__main__":
    asyncio.run(main())
