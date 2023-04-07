

# Open the file for reading
with open('information.txt', 'r') as file:
    # Initialize an empty list to store the dictionaries
    molecular = []
    # Initialize an empty dictionary to store the current person's information
    current_molecular = {}
    # Loop over each line in the file
    for line in file:
        # Strip any leading or trailing whitespace
        line = line.strip()
        # If the line is blank, it means we've finished reading the current person's information
        if not line:
            # Append the current person's dictionary to the list
            molecular.append(current_molecular)
            # Reset the current person's dictionary to empty for the next person's information
            current_molecular = {}
        else:
            # Split the line into key and value using the '=' separator
            key, value = line.split('=')
            # Store the key-value pair in the current person's dictionary
            current_molecular[key] = value

    # Append the last person's dictionary to the list (if any)
    if current_molecular:
        molecular.append(current_molecular)

# Print the list of dictionaries
#print(molecular)

for line in molecular:
    print(line['INDEX_START'])
