Path,Method,Operation ID,Summary,Description,Tags,Security Required
/,GET,root__get,Root,"Root endpoint.

Returns:
    dict[str, str]: Welcome message with API information...",,No
/health,GET,healthCheck,Health Check,"Comprehensive health check endpoint that verifies all system dependencies including database, cache,...",,No
/api/v1/auth/register,POST,registerUser,Register New User,"Create a new user account with email, username, and password....",Authentication,No
/api/v1/auth/login,POST,loginUser,User Login,Authenticate user with username/email and password to receive access token....,Authentication,No
/api/v1/auth/logout,POST,logout_api_v1_auth_logout_post,Logout,"Logout current user (deactivate session).

Args:
    current_user (User): Current authenticated user...",Authentication,Yes
/api/v1/auth/me,GET,getCurrentUserProfile,Get Current User Profile,Retrieve the authenticated user's profile information....,Authentication,Yes
/api/v1/admin/login,GET,adminLoginPage,Admin Login Page,Render the admin login page with authentication form...,Admin Auth,No
/api/v1/admin/login,POST,adminLogin,Admin Login,Authenticate admin user and create session with cookie...,Admin Auth,No
/api/v1/admin/logout,GET,adminLogout,Admin Logout,Log out admin user by clearing authentication cookie...,Admin Auth,No
/api/v1/admin/dashboard,GET,adminDashboard,Admin Dashboard,Render the main admin dashboard with navigation and overview...,Admin Auth,No
/api/v1/admin/manufacturing-types,GET,list_manufacturing_types_api_v1_admin_manufacturing_types_get,List Manufacturing Types,List all manufacturing types....,Admin Manufacturing,Yes
/api/v1/admin/manufacturing-types/create,GET,create_manufacturing_type_form_api_v1_admin_manufacturing_types_create_get,Create Manufacturing Type Form,Render create manufacturing type form....,Admin Manufacturing,Yes
/api/v1/admin/manufacturing-types/create,POST,create_manufacturing_type_api_v1_admin_manufacturing_types_create_post,Create Manufacturing Type,Handle create manufacturing type submission....,Admin Manufacturing,Yes
/api/v1/admin/manufacturing-types/{id}/edit,GET,edit_manufacturing_type_form_api_v1_admin_manufacturing_types__id__edit_get,Edit Manufacturing Type Form,Render edit manufacturing type form....,Admin Manufacturing,Yes
/api/v1/admin/manufacturing-types/{id}/edit,POST,edit_manufacturing_type_api_v1_admin_manufacturing_types__id__edit_post,Edit Manufacturing Type,Handle edit manufacturing type submission....,Admin Manufacturing,Yes
/api/v1/admin/manufacturing-types/{id}/delete,POST,delete_manufacturing_type_api_v1_admin_manufacturing_types__id__delete_post,Delete Manufacturing Type,Handle delete manufacturing type....,Admin Manufacturing,Yes
/api/v1/admin/orders,GET,adminListOrders,List Orders,List all orders with optional filtering by status and search term. Supports pagination....,Admin Orders,Yes
/api/v1/admin/orders/{id},GET,viewOrder,View Order,"Display detailed order information including customer, items, and quote...",Admin Orders,Yes
/api/v1/admin/orders/{id}/status,POST,updateOrderStatus,Update Order Status,"Update the status of an order (confirmed, production, shipped, installed)...",Admin Orders,Yes
/api/v1/admin/customers,GET,adminListCustomers,List Customers,"List all customers with optional filtering by status, type, and search term. Supports pagination....",Admin Customers,Yes
/api/v1/admin/customers,POST,adminCreateCustomer,Create Customer,Create a new customer from form submission...,Admin Customers,Yes
/api/v1/admin/customers/new,GET,newCustomerForm,New Customer Form,Display form for creating a new customer...,Admin Customers,Yes
/api/v1/admin/customers/{id},GET,viewCustomer,View Customer,Display detailed customer information...,Admin Customers,Yes
/api/v1/admin/customers/{id}/edit,GET,editCustomerForm,Edit Customer Form,Display form for editing an existing customer...,Admin Customers,Yes
/api/v1/admin/customers/{id}/edit,POST,adminUpdateCustomer,Update Customer,Update an existing customer from form submission...,Admin Customers,Yes
/api/v1/admin/customers/{id}/delete,POST,deleteCustomer,Delete Customer,Delete a customer record...,Admin Customers,Yes
/api/v1/admin/documentation,GET,documentation_api_v1_admin_documentation_get,Documentation,Display system documentation....,Admin Documentation,Yes
/api/v1/admin/settings,GET,settings_page_api_v1_admin_settings_get,Settings Page,Render settings page with shared admin context....,Admin Settings,Yes
/api/v1/admin/settings/update-username,POST,update_username_api_v1_admin_settings_update_username_post,Update Username,Handle username update form submission....,Admin Settings,Yes
/api/v1/admin/settings/update-password,POST,update_password_api_v1_admin_settings_update_password_post,Update Password,Handle password update form submission....,Admin Settings,Yes
/api/v1/users/,GET,listUsers,List Users with Filters,"List all users with optional filtering by active status, superuser status, and search term. Supports...",Users,Yes
/api/v1/users/{user_id},GET,get_user_api_v1_users__user_id__get,Get User,"Get user by ID with caching.

Rate limit: 20 requests per minute.
Cache TTL: 5 minutes.

Args:
    u...",Users,Yes
/api/v1/users/{user_id},PATCH,update_user_api_v1_users__user_id__patch,Update User,"Update user information.

Args:
    user_id (PositiveInt): User ID
    user_update (UserUpdate): Use...",Users,Yes
/api/v1/users/{user_id},DELETE,delete_user_api_v1_users__user_id__delete,Delete User,"Delete user (superuser only).

Args:
    user_id (PositiveInt): User ID
    current_superuser (User)...",Users,Yes
/api/v1/users/bulk,POST,createUsersBulk,Create Multiple Users in Bulk,"Create multiple users in a single atomic transaction. If any user creation fails, the entire transac...",Users,Yes
/api/v1/export/my-data,GET,exportMyData,Export My Data,Export the authenticated user's data in JSON format (GDPR compliance)....,Export,Yes
/api/v1/export/users/json,GET,exportUsersJson,Export All Users (JSON),Export all users data in JSON format (superuser only)....,Export,Yes
/api/v1/export/users/csv,GET,exportUsersCsv,Export All Users (CSV),Export all users data in CSV format (superuser only)....,Export,Yes
/api/v1/dashboard/,GET,getDashboard,Admin Dashboard,Main admin dashboard with statistics and data entry forms....,Dashboard,Yes
/api/v1/dashboard/data-entry,GET,getDataEntryForm,Data Entry Form,Form for entering new data into the system....,Dashboard,Yes
/api/v1/dashboard/stats,GET,getDashboardStats,Dashboard Statistics,Get real-time dashboard statistics with 1-minute caching for optimal performance....,Dashboard,Yes
/api/v1/metrics/database,GET,getDatabaseMetrics,Get Database Connection Pool Metrics,"Retrieve real-time database connection pool statistics including pool size, checked in/out connectio...",Metrics,Yes
/api/v1/manufacturing-types/,GET,listManufacturingTypes,List Manufacturing Types,List all manufacturing types with optional filtering by active status and category. Supports paginat...,Manufacturing Types,Yes
/api/v1/manufacturing-types/,POST,createManufacturingType,Create Manufacturing Type,Create a new manufacturing type (superuser only)...,Manufacturing Types,Yes
/api/v1/manufacturing-types/{type_id},GET,getManufacturingType,Get Manufacturing Type,Get a single manufacturing type by ID...,Manufacturing Types,Yes
/api/v1/manufacturing-types/{type_id},PATCH,updateManufacturingType,Update Manufacturing Type,Update an existing manufacturing type (superuser only)...,Manufacturing Types,Yes
/api/v1/manufacturing-types/{type_id},DELETE,deleteManufacturingType,Delete Manufacturing Type,Deactivate a manufacturing type (superuser only). This is a soft delete that sets is_active to false...,Manufacturing Types,Yes
/api/v1/attribute-nodes/,GET,listAttributeNodes,List Attribute Nodes,List attribute nodes with optional filtering by manufacturing type...,Attribute Nodes,Yes
/api/v1/attribute-nodes/,POST,createAttributeNode,Create Attribute Node,Create a new attribute node (superuser only)...,Attribute Nodes,Yes
/api/v1/attribute-nodes/{node_id},GET,getAttributeNode,Get Attribute Node,Get a single attribute node by ID...,Attribute Nodes,Yes
/api/v1/attribute-nodes/{node_id},PATCH,updateAttributeNode,Update Attribute Node,Update an existing attribute node (superuser only)...,Attribute Nodes,Yes
/api/v1/attribute-nodes/{node_id},DELETE,deleteAttributeNode,Delete Attribute Node,Delete an attribute node and all its descendants (superuser only)...,Attribute Nodes,Yes
/api/v1/attribute-nodes/{node_id}/children,GET,getAttributeNodeChildren,Get Child Nodes,Get direct children of an attribute node...,Attribute Nodes,Yes
/api/v1/attribute-nodes/{node_id}/tree,GET,getAttributeNodeTree,Get Node Subtree,Get full subtree of descendants for an attribute node using LTREE...,Attribute Nodes,Yes
/api/v1/configurations/,GET,listConfigurations,List Configurations,List user's configurations with pagination. Superusers can see all configurations....,Configurations,Yes
/api/v1/configurations/,POST,createConfiguration,Create Configuration,Create a new product configuration...,Configurations,Yes
/api/v1/configurations/{config_id},GET,getConfiguration,Get Configuration,Get a configuration with all its selections...,Configurations,Yes
/api/v1/configurations/{config_id},PATCH,updateConfiguration,Update Configuration,Update configuration name and description...,Configurations,Yes
/api/v1/configurations/{config_id},DELETE,deleteConfiguration,Delete Configuration,Delete a configuration and all its selections...,Configurations,Yes
/api/v1/configurations/{config_id}/selections,PATCH,updateConfigurationSelections,Update Configuration Selections,Update attribute selections for a configuration...,Configurations,Yes
/api/v1/quotes/,GET,listQuotes,List Quotes,List user's quotes with pagination. Superusers can see all quotes....,Quotes,Yes
/api/v1/quotes/,POST,createQuote,Generate Quote,Generate a quote from a configuration with automatic price calculation...,Quotes,Yes
/api/v1/quotes/{quote_id},GET,getQuote,Get Quote,Get a single quote by ID...,Quotes,Yes
/api/v1/templates/,GET,listTemplates,List Templates,List public templates with pagination...,Templates,Yes
/api/v1/templates/,POST,createTemplate,Create Template,Create a new template from a configuration (superuser only)...,Templates,Yes
/api/v1/templates/{template_id},GET,getTemplate,Get Template,Get a template with all its selections...,Templates,Yes
/api/v1/templates/{template_id}/apply,POST,applyTemplate,Apply Template,Apply a template to create a new configuration...,Templates,Yes
/api/v1/customers/,GET,listCustomers,List Customers,List all customers with pagination (superuser only)...,Customers,Yes
/api/v1/customers/,POST,createCustomer,Create Customer,Create a new customer (superuser only)...,Customers,Yes
/api/v1/customers/{customer_id},GET,getCustomer,Get Customer,Get a single customer by ID (superuser only)...,Customers,Yes
/api/v1/customers/{customer_id},PATCH,updateCustomer,Update Customer,Update an existing customer (superuser only)...,Customers,Yes
/api/v1/orders/,GET,listOrders,List Orders,List user's orders with pagination. Superusers can see all orders....,Orders,Yes
/api/v1/orders/,POST,createOrder,Create Order,Create an order from an accepted quote...,Orders,Yes
/api/v1/orders/{order_id},GET,getOrder,Get Order,Get a single order by ID with all items...,Orders,Yes
/api/v1/admin/hierarchy/,GET,hierarchyDashboard,Hierarchy Management Dashboard,View and manage hierarchical attribute trees for manufacturing types...,Admin Hierarchy,Yes
/api/v1/admin/hierarchy/node/create,GET,createNodeForm,Create Node Form,Display form for creating a new attribute node...,Admin Hierarchy,Yes
/api/v1/admin/hierarchy/node/save,POST,saveNode,Save Node,Create or update an attribute node with validation...,Admin Hierarchy,Yes
/api/v1/admin/hierarchy/node/{node_id}/edit,GET,editNodeForm,Edit Node Form,Display form for editing an existing attribute node...,Admin Hierarchy,Yes
/api/v1/admin/hierarchy/node/{node_id}/delete,POST,deleteNode,Delete Node,Delete an attribute node (must not have children)...,Admin Hierarchy,Yes
/api/v1/admin/policies/,POST,add_policy_api_v1_admin_policies__post,Add Policy,"Add a new policy rule.

Requires superadmin privileges. Creates a new policy rule in the Casbin
poli...",Policy Management,Yes
/api/v1/admin/policies/,DELETE,remove_policy_api_v1_admin_policies__delete,Remove Policy,"Remove a policy rule.

Requires superadmin privileges. Removes an existing policy rule from the
Casb...",Policy Management,Yes
/api/v1/admin/policies/assign-customer,POST,assign_customer_to_user_api_v1_admin_policies_assign_customer_post,Assign Customer To User,"Assign customer access to a user.

Requires superadmin privileges. Assigns customer access to a user...",Policy Management,Yes
/api/v1/admin/policies/assign-customer,DELETE,remove_customer_assignment_api_v1_admin_policies_assign_customer_delete,Remove Customer Assignment,"Remove customer assignment from a user.

Requires superadmin privileges. Removes customer access fro...",Policy Management,Yes
/api/v1/admin/policies/assign-role,POST,assign_role_to_user_api_v1_admin_policies_assign_role_post,Assign Role To User,"Assign role to a user.

Requires superadmin privileges. Assigns a role to a user and updates
both th...",Policy Management,Yes
/api/v1/admin/policies/summary,GET,get_policy_summary_api_v1_admin_policies_summary_get,Get Policy Summary,"Get a summary of current policies and assignments.

Requires superadmin privileges. Returns a compre...",Policy Management,Yes
/api/v1/admin/policies/backup,POST,backup_policies_api_v1_admin_policies_backup_post,Backup Policies,"Create a backup of all current policies.

Requires superadmin privileges. Creates a complete backup ...",Policy Management,Yes
/api/v1/admin/policies/restore,POST,restore_policies_api_v1_admin_policies_restore_post,Restore Policies,"Restore policies from a backup.

Requires superadmin privileges. Restores all policies from a backup...",Policy Management,Yes
/api/v1/admin/policies/validate,POST,validate_policies_api_v1_admin_policies_validate_post,Validate Policies,"Validate current policies for conflicts and issues.

Requires superadmin privileges. Performs compre...",Policy Management,Yes
/api/v1/admin/policies/seed,POST,seed_initial_policies_api_v1_admin_policies_seed_post,Seed Initial Policies,"Seed initial policies for default roles.

Requires superadmin privileges. Creates the initial policy...",Policy Management,Yes
/api/v1/admin/policies/user-assignments/{user_email},GET,get_user_assignments_api_v1_admin_policies_user_assignments__user_email__get,Get User Assignments,"Get all assignments for a specific user.

Requires superadmin privileges. Returns all customer assig...",Policy Management,Yes
/api/v1/entry/profile/schema/{manufacturing_type_id},GET,getProfileSchema,Get Profile Form Schema,Get dynamic form schema for profile data entry based on manufacturing type...,Entry Pages,Yes
/api/v1/entry/profile/save,POST,saveProfileData,Save Profile Data,Save profile configuration data and create configuration record...,Entry Pages,Yes
/api/v1/entry/profile/preview/{configuration_id},GET,getProfilePreview,Get Profile Preview,Get preview table data for a configuration...,Entry Pages,Yes
/api/v1/entry/profile/evaluate-conditions,POST,evaluateDisplayConditions,Evaluate Display Conditions,Evaluate conditional field visibility based on form data...,Entry Pages,Yes
/api/v1/entry/profile,GET,profileEntryPage,Profile Entry Page,Render the profile data entry page...,Entry Pages,Yes
/api/v1/entry/accessories,GET,accessoriesEntryPage,Accessories Entry Page,Render the accessories data entry page (scaffold)...,Entry Pages,Yes
/api/v1/entry/glazing,GET,glazingEntryPage,Glazing Entry Page,Render the glazing data entry page (scaffold)...,Entry Pages,Yes
