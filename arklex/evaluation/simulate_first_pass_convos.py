import json
import random
from arklex.evaluation.get_documents import load_docs
from arklex.evaluation.chatgpt_utils import (chatgpt_chatbot, query_chatbot, filter_convo, adjust_goal,
                                               flip_hist, generate_goals, format_chat_history_str, flip_hist_content_only)
import requests


def generate_synthetic_data(documents, synthetic_data_params):
    """
    Generate synthetic data for testing.
    
    Args:
        documents (list): List of documents
        synthetic_data_params (dict): Parameters for synthetic data generation
        
    Returns:
        list: List of synthetic data items
    """
    # For research assistant, we can generate research questions
    research_questions = [
        {
            "goal": "Find recent papers on machine learning for healthcare applications",
            "expected_sources": ["ArXiv", "PubMed"],
            "complexity": "medium"
        },
        {
            "goal": "Research the latest developments in quantum computing algorithms",
            "expected_sources": ["ArXiv"],
            "complexity": "high"
        },
        {
            "goal": "Find studies on the effectiveness of mindfulness meditation for stress reduction",
            "expected_sources": ["PubMed"],
            "complexity": "medium"
        },
        {
            "goal": "Research the environmental impact of electric vehicles compared to traditional vehicles",
            "expected_sources": ["ArXiv", "PubMed"],
            "complexity": "medium"
        },
        {
            "goal": "Find papers discussing natural language processing techniques for sentiment analysis",
            "expected_sources": ["ArXiv"],
            "complexity": "medium"
        }
    ]
    
    # Select the number of goals specified in synthetic_data_params
    num_goals = min(synthetic_data_params.get('num_goals', 3), len(research_questions))
    selected_goals = research_questions[:num_goals]
    
    return selected_goals


def check_goal_completion(goal, convo):
    convo_str = format_chat_history_str(flip_hist_content_only(convo[2:]))
    prompt = f"Here is a conversation between a user and a customer service chatbot assistant:\n{convo_str}\n\nThe user's goal is the following: {goal}\nOutput False if the user needs to learn more information regarding their goal. Output True otherwise. Only onput True or False and nothing else."
    output = chatgpt_chatbot([{'role': 'user', 'content': prompt}])
    return output == "True"

def conversation(model_api, goal, summary, model_params, synthetic_data_params, env_config):
    history = []
    instructional_prompt = f'Replicate the writing behavior of a human customer. You are interacting with a customer service chatbot for the following company: {summary}\nYou have the following goal when interacting with this chatbot:\n{goal}\n Have a conversation with the chatbot while trying to achieve this goal. Make sure the conversation is natural. For example, if the chatbot asks you a question you should answer it.'
    start_text = "Humans write short questions with typos and a neutral sentiment. Here are some examples of what a human customer would type: [how much is it?, Can you send info to my email, yes I need a job, want to check both proposals to rent and buy, How much does it cost a [PRODUCT_HERE], Im interested in [PRODUCT_HERE], hi i would like to rent out [PRODUCT_HERE] but im wondering which countries are available for rental]. Replicate the writing behavior of a human customer and begin the conversation with a question to achieve your goal."
    history.append({'role': 'system','content': instructional_prompt})
    history.append({'role': 'user', 'content': start_text})
    chatbot_history = []

    for i in range(synthetic_data_params['max_turns']):
        output = chatgpt_chatbot(history) 
        history.append({'role': 'assistant', 'content': output})
        chatbot_history.append({'role': 'assistant', 'content': output})
        response_data = query_chatbot(model_api, chatbot_history, model_params, env_config)
        answer = response_data["answer"]
        answer = answer.replace('\n', ' ')
        model_params = response_data["parameters"]
        pred_intent = response_data['parameters']['nlu_records'][-1]['pred_intent']
        history[-1]['intent'] = pred_intent

        history.append({'role': 'user', 'content': answer})
        chatbot_history.append({'role': 'user', 'content': answer})
        if i > 2 and check_goal_completion(goal, history.copy()):
            history.append({'goal_completetion': True})
            break
    
    if not history[-1].get('goal_completetion', False):
        history.append({'goal_completetion': False})
    history.append({'trajectory': model_params["history"]})
    return history

def generate_conversations(model_api, goals, summary, model_params, synthetic_data_params, env_config):
    convos = []
    # for i in range(synthetic_data_params['num_convos']):
    for goal in goals:
        # goal = random.choice(goals)
        convo = conversation(model_api, goal, summary, model_params, synthetic_data_params, env_config)
        convos.append(flip_hist(filter_convo(convo, filter_turns=False)))
    return convos

def simulate_conversations(model_api, model_params, synthetic_data_params, config):
    """
    Simulate conversations with the model.
    
    Args:
        model_api (str): URL of the model API
        model_params (dict): Parameters for the model
        synthetic_data_params (dict): Parameters for synthetic data generation
        config (dict): Configuration dictionary
        
    Returns:
        tuple: (first_pass_data, goals)
    """
    try:
        # Load documents
        documents = load_docs(config['documents_dir'], config, synthetic_data_params['num_goals'] * 2)
        
        # Generate synthetic data
        print("Generating synthetic data...")
        synthetic_data = generate_synthetic_data(documents, synthetic_data_params)
        
        # Simulate conversations
        print("Simulating conversations...")
        first_pass_data = []
        
        # Define the endpoints to try
        # Make sure we don't duplicate the path
        if model_api.endswith('/'):
            model_api = model_api[:-1]  # Remove trailing slash
            
        # Define endpoints to try
        endpoints_to_try = [
            f"{model_api}/eval/chat",  # Original endpoint
            f"{model_api}/chat",       # Simplified endpoint
            model_api                  # Base endpoint
        ]
        
        print(f"Will try the following endpoints: {endpoints_to_try}")
        
        # Check if API server is running
        for endpoint in endpoints_to_try:
            try:
                print(f"Testing API endpoint with POST: {endpoint}")
                test_response = requests.post(
                    endpoint,
                    json={
                        "history": [{"role": "user", "content": "Hello"}],
                        "parameters": {},
                        "workers": config.get("workers", []),
                        "tools": config.get("tools", [])
                    },
                    timeout=10
                )
                print(f"API test response: {test_response.status_code} - {test_response.text[:100]}...")
                
                if test_response.status_code == 200:
                    print(f"API endpoint {endpoint} is working correctly!")
                    # Use only this endpoint for all conversations
                    endpoints_to_try = [endpoint]
                    break
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not connect to API at {endpoint}. Error: {str(e)}")
        
        # If no endpoint worked, print a warning
        if len(endpoints_to_try) > 1:
            print("Warning: Could not find a working API endpoint. Will try all endpoints for each conversation.")
        
        for i, goal in enumerate(synthetic_data):
            try:
                print(f"Simulating conversation {i+1}/{len(synthetic_data)}...")
                print(f"Goal: {goal}")
                
                # Try different endpoints
                response = None
                used_endpoint = None
                
                for endpoint in endpoints_to_try:
                    try:
                        print(f"Trying endpoint: {endpoint}")
                        response = requests.post(
                            endpoint,
                            json={
                                "history": [{"role": "user", "content": goal["goal"]}],
                                "parameters": {},
                                "workers": config.get("workers", []),
                                "tools": config.get("tools", [])
                            },
                            timeout=10  # Add timeout to avoid hanging
                        )
                        print(f"Response status: {response.status_code}")
                        print(f"Response content: {response.text[:100]}...")
                        
                        if response.status_code == 200:
                            used_endpoint = endpoint
                            break
                    except requests.exceptions.RequestException as e:
                        print(f"Error with endpoint {endpoint}: {str(e)}")
                
                # Process the response if we got one
                if response and used_endpoint:
                    print(f"Successfully used endpoint: {used_endpoint}")
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            first_pass_data.append({
                                "goal": goal,
                                "response": response_data
                            })
                        except json.JSONDecodeError:
                            print(f"Error: Could not parse JSON response: {response.text}")
                            first_pass_data.append({
                                "goal": goal,
                                "response": {"error": "Invalid JSON response", "text": response.text}
                            })
                    else:
                        print(f"Error: API returned status code {response.status_code}")
                        first_pass_data.append({
                            "goal": goal,
                            "response": {"error": f"API returned status code {response.status_code}", "text": response.text}
                        })
                else:
                    print("Error: Could not connect to any endpoint")
                    first_pass_data.append({
                        "goal": goal,
                        "response": {"error": "Could not connect to any endpoint"}
                    })
            except Exception as e:
                print(f"Error simulating conversation {i+1}: {str(e)}")
                first_pass_data.append({
                    "goal": goal,
                    "response": {"error": f"Simulation error: {str(e)}"}
                })
        
        return first_pass_data, synthetic_data
    except Exception as e:
        print("Generate conversations failed")
        print("Error: ", str(e))
        return [], []

if __name__ == "__main__":
    model_api = "http://adaptation.cs.columbia.edu:55231/qa/richtech/v1alpha1"
    synthetic_data_params = {'num_convos': 5, 'num_goals': 3, 'max_turns': 10}
    model_params = {}
    convos  = simulate_conversations(model_api, model_params, synthetic_data_params)
    with open('p1_sample_convos.json', 'w') as f:
        json.dump(convos, f, indent=5)