from database.database  import  Database,Dialogue
conversations = [
    {"role": "user", "message": "What is the weather like today?"},
    {"role": "server", "message": "The weather is sunny and 25°C."},
    {"role": "user", "message": "Great! Thank you."}
]
db = Database()
task_id = db.create_dialogue("俄乌冲突", ["subquery3"], conversations)

Dialogue()
add_subquery_to_dialogue()