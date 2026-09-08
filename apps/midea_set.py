import sys

from midea_beautiful import appliance_state, connect_to_cloud

account, password, device_id, attr, raw_value = sys.argv[1:6]

try:
    value = int(raw_value)
except ValueError:
    value = raw_value

cloud = connect_to_cloud(account=account, password=password)
appliance = appliance_state(cloud=cloud, use_cloud=True, appliance_id=device_id)
appliance.set_state(cloud=cloud, **{attr: value})
print("OK")
