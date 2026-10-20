def record_user_details(email,name = "Not provided", notes= "Not provided"):
    with open("agents/1_foundations/Dev_Handson/user_details.txt",encoding="utf-8") as f:
        f.write(f"Recording {email} for the user {name}")

record_user_details={
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}
