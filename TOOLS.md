# Tool catalogue — openstack-mcp-guarded

> Full upstream catalogue: **135 tools** · visible in read-only mode: **66** · blocked: **69**

Sources: upstream `python-openstackmcp-server` (compute, image, identity, network, block storage, session) + extra tools in this repo (Octavia load balancers, Designate DNS, ops/Heat).

---

## ✅ Allowed in read-only mode (default)

| Tool | Category | Description |
|---|---|---|
| `get_amphorae` | Load Balancer (Octavia) | List amphora instances (requires admin role). |
| `get_attachment_details` | Block Storage | Get detailed information about a specific attachment. |
| `get_attachments` | Block Storage | Get the list of attachments. |
| `get_availability_zones` | Ops / Heat | List compute availability zones (detailed=True adds host info, admin only). |
| `get_cloud_config` | Session | Provide cloud configuration with secrets masked of current user's config file. |
| `get_cloud_name` | Session | Return the currently selected cloud name. |
| `get_cloud_names` | Session | List available cloud configurations. |
| `get_compute_quotas` | Ops / Heat | Get compute quotas for a project (optionally with usage). |
| `get_compute_services` | Ops / Heat | List compute services (nova-compute, scheduler...) with status (admin only). |
| `get_dns_limits` | DNS (Designate) | List Designate API limits. |
| `get_dns_quota` | DNS (Designate) | Get Designate quotas for a project. |
| `get_dns_recordset_detail` | DNS (Designate) | Get detailed information about a specific recordset. |
| `get_dns_recordsets` | DNS (Designate) | List recordsets, optionally filtered by zone, type (A/AAAA/CNAME/MX/TXT/SRV/PTR/CAA/NS) or name. |
| `get_dns_zone_detail` | DNS (Designate) | Get detailed information about a specific DNS zone. |
| `get_dns_zone_exports` | DNS (Designate) | List DNS zone export jobs. |
| `get_dns_zone_imports` | DNS (Designate) | List DNS zone import jobs. |
| `get_dns_zone_nameservers` | DNS (Designate) | List nameservers assigned to a DNS zone. |
| `get_dns_zone_transfer_requests` | DNS (Designate) | List DNS zone transfer requests. |
| `get_dns_zones` | DNS (Designate) | List DNS zones with optional filters. |
| `get_domain` | Identity | Get a domain. |
| `get_domains` | Identity | Get the list of Identity domains. |
| `get_flavors` | Compute | Get flavors (server hardware configurations). |
| `get_floating_ips` | Network | Get the list of Floating IPs with optional filtering. |
| `get_health_monitors` | Load Balancer (Octavia) | List health monitors, optionally filtered by pool. |
| `get_heat_stack_detail` | Ops / Heat | Get detailed information about a stack (incl. |
| `get_heat_stack_events` | Ops / Heat | List events of a stack (optionally of a single resource). |
| `get_heat_stack_resources` | Ops / Heat | List resources of a stack. |
| `get_heat_stack_template` | Ops / Heat | Get the template of a stack. |
| `get_heat_stacks` | Ops / Heat | List Heat stacks with optional status/name filters. |
| `get_hypervisor_uptime` | Ops / Heat | Get uptime of a hypervisor (admin only). |
| `get_hypervisors` | Ops / Heat | List hypervisors with CPU/memory/disk stats (admin only). |
| `get_image` | Image | Get an OpenStack image by ID. |
| `get_images` | Image | Get the list of OpenStack images with optional filtering. |
| `get_keypairs` | Ops / Heat | List key pairs (optionally filter by name). |
| `get_listener_statistics` | Load Balancer (Octavia) | Get traffic statistics for a specific listener. |
| `get_listeners` | Load Balancer (Octavia) | List listeners, optionally filtered by load balancer or protocol. |
| `get_load_balancer_detail` | Load Balancer (Octavia) | Get detailed information about a specific load balancer. |
| `get_load_balancer_flavors` | Load Balancer (Octavia) | List load balancer flavors. |
| `get_load_balancer_providers` | Load Balancer (Octavia) | List available load balancer providers (e.g. |
| `get_load_balancer_statistics` | Load Balancer (Octavia) | Get traffic statistics (bytes, connections, errors) for a load balancer. |
| `get_load_balancers` | Load Balancer (Octavia) | List load balancers with optional status/name filters. |
| `get_network_detail` | Network | Get detailed information about a specific Network. |
| `get_networks` | Network | Get the list of Networks with optional filtering. |
| `get_pool_members` | Load Balancer (Octavia) | List members of a specific pool. |
| `get_pools` | Load Balancer (Octavia) | List pools, optionally filtered by load balancer or protocol. |
| `get_port_allowed_address_pairs` | Network | Get allowed address pairs configured on a port. |
| `get_port_detail` | Network | Get detailed information about a specific Port. |
| `get_ports` | Network | Get the list of Ports with optional filtering. |
| `get_project` | Identity | Get a project. |
| `get_projects` | Identity | Get the list of Identity projects. |
| `get_region` | Identity | Get a region. |
| `get_regions` | Identity | Get the list of Identity regions. |
| `get_router_detail` | Network | Get detailed information about a specific Router. |
| `get_router_interfaces` | Network | List interfaces attached to a Router. |
| `get_routers` | Network | Get the list of Routers with optional filtering. |
| `get_security_group_detail` | Network | Get detailed information about a specific Security Group. |
| `get_security_groups` | Network | Get the list of Security Groups with optional filtering. |
| `get_server` | Compute | Get a specific Compute server. |
| `get_server_actions` | Ops / Heat | List lifecycle actions/events of a server (audit trail). |
| `get_server_groups` | Ops / Heat | List server groups (affinity/anti-affinity scheduling). |
| `get_servers` | Compute | Get the list of Compute servers. |
| `get_subnet_detail` | Network | Get detailed information about a specific Subnet. |
| `get_subnets` | Network | Get the list of Subnets with optional filtering. |
| `get_volume_details` | Block Storage | Get detailed information about a specific volume. |
| `get_volumes` | Block Storage | Get the list of Block Storage volumes. |
| `set_cloud_name` | Session | Set cloud name to use for later connections. |

---

## ⛔ Blocked by policy

Hidden from the model (`on_list_tools`) and hard-blocked on direct invocation (`on_call_tool`). Audit line on stderr for every attempt.

| Tool | Category | What it would do |
|---|---|---|
| `action_server` | Compute | Perform an action on a Compute server. |
| `add_router_interface` | Network | Add an interface to a Router by subnet or port. |
| `assign_first_available_floating_ip` | Network | Assign the first available floating IP from a network to a port. |
| `attach_volume` | Compute | Attach a volume to a Compute server. |
| `create_dns_recordset` | DNS (Designate) | Create a recordset in a zone (type: A/AAAA/CNAME/MX/TXT/SRV/PTR/NS/CAA). |
| `create_dns_zone` | DNS (Designate) | Create a DNS zone (e.g. |
| `create_domain` | Identity | Create a new domain. |
| `create_floating_ip` | Network | Create a new Floating IP. |
| `create_floating_ips_bulk` | Network | Create multiple floating IPs on the specified external network. |
| `create_health_monitor` | Load Balancer (Octavia) | Create a health monitor for a pool (type: HTTP/HTTPS/TCP/UDP/TLS-HELLO/PING). |
| `create_heat_stack` | Ops / Heat | Create a Heat stack from a template dict (YAML parsed). |
| `create_image` | Image | Create a new Openstack image. |
| `create_keypair` | Ops / Heat | Create an SSH keypair (returns the private key ONCE). |
| `create_listener` | Load Balancer (Octavia) | Create a listener on a load balancer (protocol: TCP/HTTP/HTTPS/TERMINATED_HTTPS/UDP). |
| `create_load_balancer` | Load Balancer (Octavia) | Create a new load balancer. |
| `create_network` | Network | Create a new Network. |
| `create_pool` | Load Balancer (Octavia) | Create a pool on a load balancer (lb_algorithm: ROUND_ROBIN/LEAST_CONNECTIONS/SOURCE_IP). |
| `create_pool_member` | Load Balancer (Octavia) | Add a member (backend server) to a pool. |
| `create_port` | Network | Create a new Port. |
| `create_project` | Identity | Create a new project. |
| `create_region` | Identity | Create a new region. |
| `create_router` | Network | Create a new Router. |
| `create_security_group` | Network | Create a new Security Group. |
| `create_server` | Compute | Create a new Compute server. |
| `create_server_group` | Ops / Heat | Create a server group (policies: affinity/anti-affinity/soft-*, ...). |
| `create_subnet` | Network | Create a new Subnet. |
| `create_volume` | Block Storage | Create a new volume. |
| `delete_dns_recordset` | DNS (Designate) | Delete a recordset. |
| `delete_dns_zone` | DNS (Designate) | Delete a DNS zone. |
| `delete_domain` | Identity | Delete a domain. |
| `delete_floating_ip` | Network | Delete a Floating IP. |
| `delete_health_monitor` | Load Balancer (Octavia) | Delete a health monitor. |
| `delete_heat_stack` | Ops / Heat | Delete a Heat stack. |
| `delete_image` | Image | Delete an OpenStack image. |
| `delete_keypair` | Ops / Heat | Delete an SSH keypair. |
| `delete_listener` | Load Balancer (Octavia) | Delete a listener. |
| `delete_load_balancer` | Load Balancer (Octavia) | Delete a load balancer (cascade also removes listeners/pools/members). |
| `delete_network` | Network | Delete a Network. |
| `delete_pool` | Load Balancer (Octavia) | Delete a pool. |
| `delete_pool_member` | Load Balancer (Octavia) | Remove a member from a pool. |
| `delete_port` | Network | Delete a Port. |
| `delete_project` | Identity | Delete a project. |
| `delete_region` | Identity | Delete a region. |
| `delete_router` | Network | Delete a Router. |
| `delete_security_group` | Network | Delete a Security Group. |
| `delete_server` | Compute | Delete a Compute server. |
| `delete_server_group` | Ops / Heat | Delete a server group. |
| `delete_subnet` | Network | Delete a Subnet. |
| `delete_volume` | Block Storage | Delete a volume. |
| `detach_volume` | Compute | Detach a volume from a Compute server. |
| `extend_volume` | Block Storage | Extend a volume to a new size. |
| `failover_load_balancer` | Load Balancer (Octavia) | Trigger failover of a load balancer (rebuilds its amphorae). |
| `remove_router_interface` | Network | Remove an interface from a Router by subnet or port. |
| `set_port_binding` | Network | Set binding attributes for a port. |
| `update_dns_recordset` | DNS (Designate) | Update a recordset (e.g. |
| `update_dns_zone` | DNS (Designate) | Update DNS zone attributes. |
| `update_domain` | Identity | Update a domain. |
| `update_floating_ip` | Network | Update Floating IP attributes. Only provided parameters are changed; omitted parameters remain untouched. |
| `update_heat_stack` | Ops / Heat | Update an existing Heat stack with a new template. |
| `update_load_balancer` | Load Balancer (Octavia) | Update load balancer attributes. |
| `update_network` | Network | Update an existing Network. |
| `update_pool_member` | Load Balancer (Octavia) | Update a pool member (e.g. |
| `update_port` | Network | Update an existing Port. Only provided parameters are changed; omitted parameters remain untouched. |
| `update_project` | Identity | Update a project. |
| `update_region` | Identity | Update a region. |
| `update_router` | Network | Update Router attributes atomically. Only provided parameters are changed; omitted parameters remain untouched. |
| `update_security_group` | Network | Update an existing Security Group. |
| `update_server` | Compute | Update a Compute server's name, hostname, or description. |
| `update_subnet` | Network | Update subnet attributes atomically. Only provided parameters are changed; omitted parameters remain untouched. |

---

## Regenerate

```bash
uv run python scripts/gen_tool_catalogue.py
```
