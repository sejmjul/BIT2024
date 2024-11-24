import pandas as pd
import ipaddress


def parse_and_sum_events(file_path, order_by_events=True):
    # Load the CSV with a custom separator and skip the header rows
    df = pd.read_csv(file_path, delimiter=";", skiprows=1, header=None)

    # Rename columns for clarity (first column is IP, others represent days)
    column_names = ["IP"] + [f"Day_{i}" for i in range(1, df.shape[1])]
    df.columns = column_names

    # Define the suspect IP range (excluding 147.175.0.0/16 and private IPs)
    suspect_ips = []
    total_events = {}

    # Iterate over each row in the dataframe
    for index, row in df.iterrows():
        ip_str = row['IP']

        # Skip IP if it belongs to the 147.175.0.0/16 or private ranges
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if (ip_obj in ipaddress.ip_network("147.175.0.0/16") or
                    ip_obj.is_private):
                continue  # Ignore IPs within allowed ranges
        except ValueError:
            continue  # Skip if not a valid IP

        # If it's a suspect IP, parse events from each day
        suspect_ips.append(ip_str)
        event_count = 0
        for day_col in column_names[1:]:
            event_data = row[day_col]
            if pd.notnull(event_data):  # Skip empty columns
                # Sum the events (extract the count in parentheses)
                events = event_data.split(";")
                for event in events:
                    if '(' in event and ')' in event:
                        count = int(event.split('(')[-1].split(')')[0])
                        event_count += count

        # Store total events for the suspect IP
        total_events[ip_str] = event_count
    # order by event count descending
    if order_by_events:
        total_events = sorted(total_events.items(), key=lambda x: x[1], reverse=True)
    return total_events
