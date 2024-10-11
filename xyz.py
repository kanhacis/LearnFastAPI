result = [
  {
    "email": "new@example.com",
    "first_name": "New",
    "last_name": "User",
    "name": "Other",
    "rate_type": "Per_hour",
    "rate": 100,
    "description": "string"
  },
  {
    "email": "new@example.com",
    "first_name": "New",
    "last_name": "User",
    "name": "Mechanical",
    "rate_type": "Per_hour",
    "rate": 500,
    "description": "we can discuss more details on call"
  },
  {
    "email": "raj@example.com",
    "first_name": "Raj",
    "last_name": "Patil",
    "name": "Cheif",
    "rate_type": "Half_day",
    "rate": 1000,
    "description": "string"
  }
]


workers = {}
for row in result:
    full_name = (row["first_name"], row["last_name"])
    
    print(full_name)
        
    # If worker is not in the dictionary, add them
    if full_name not in workers:
        workers[full_name] = {
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "working_areas": []
        }
        
    # Append working area info to the worker
    workers[full_name]["working_areas"].append({
        "name": row["name"],
        "rate_type": row["rate_type"],
        "rate": row["rate"],
        "description": row["description"]
    })
    
print(list(workers.values()))  
