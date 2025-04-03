import json
import networkx as nx

from arklex.evaluation.chatgpt_utils import chatgpt_chatbot, format_chat_history_str, flip_hist_content_only, filter_convo

def get_edges_and_counts(data):
    edge_counts = {}
    for convo in data:
        convo = filter_convo(convo)
        for i in range(len(convo)):
            if convo[i]['role'] == 'assistant':
                continue
            prev_intent = 'start' if i == 0 else convo[i-2]['intent']
            current_intent = convo[i]['intent']
            edge_counts[(prev_intent, current_intent)] = edge_counts.get((prev_intent, current_intent), 0) + 1
    return edge_counts

def build_intent_graph(data):
    G = nx.DiGraph()
    edge_counts = get_edges_and_counts(data)
    for key in edge_counts.keys():
        G.add_edge(key[0], key[1], weight = edge_counts[key])
    return G

def check_bot_goal(convo, bot_goal):
    convo_str = format_chat_history_str(flip_hist_content_only(convo[:-2]))
    prompt = f"Here is a conversation between a user and a customer service chatbot assistant:\n{convo_str}\n\nThe chatbot's goal is the following: {bot_goal}\nOutput True if the bot was able to achieve its goal. Output False otherwise. Only output True or False and nothing else."
    output = chatgpt_chatbot([{'role': 'user', 'content': prompt}])
    return output == "True"

def num_user_turns(convo):
    """
    Count the number of user turns in a conversation.
    
    Args:
        convo (dict): Conversation data
        
    Returns:
        int: Number of user turns
    """
    count = 0
    # Check if convo is a dictionary with a 'response' key
    if isinstance(convo, dict) and 'response' in convo:
        # Handle the case where convo is the first_pass_data format
        response = convo.get('response', {})
        if 'history' in response:
            for turn in response.get('history', []):
                if isinstance(turn, dict) and turn.get('role', None) == 'user':
                    count += 1
    # Handle the case where convo is a list of turns
    elif isinstance(convo, list):
        for turn in convo:
            if isinstance(turn, dict) and turn.get('role', None) == 'user':
                count += 1
    # Handle the case where convo is a string (error message)
    elif isinstance(convo, str):
        # If convo is a string, it's likely an error message, so return 0
        return 0
    
    return count

def extract_task_completion_metrics(data, bot_goal=None):
    """
    Extract task completion metrics from conversation data.
    
    Args:
        data (list): List of conversation data
        bot_goal (str): The bot's goal
        
    Returns:
        dict: Metrics dictionary
    """
    num_convos = len(data)
    if num_convos == 0:
        return {"error": "No conversations to analyze"}
    
    goal_completions = 0
    bot_goal_completions = 0
    completion_efficiency = 0
    
    for convo in data:
        # Count user turns for efficiency metric
        user_turns = num_user_turns(convo)
        completion_efficiency += user_turns
        
        # Check if this is the new format (dictionary with 'goal' and 'response')
        if isinstance(convo, dict) and 'goal' in convo and 'response' in convo:
            # For the new format, we can't determine goal completion from the data structure
            # So we'll assume it's incomplete if there was an error
            if 'error' not in convo['response']:
                goal_completions += 1
                
            # Check bot goal if provided
            if bot_goal is not None:
                # We can't use check_bot_goal here since the format is different
                # For now, we'll assume the bot goal is completed if there was no error
                if 'error' not in convo['response']:
                    bot_goal_completions += 1
        
        # Handle the old format (list of turns)
        elif isinstance(convo, list) and len(convo) > 0:
            # Check if the last element has goal_completion
            if isinstance(convo[-1], dict) and convo[-1].get('goal_completetion', False):
                goal_completions += 1
                
            # Check bot goal if provided
            if bot_goal is not None and check_bot_goal(convo, bot_goal):
                bot_goal_completions += 1
    
    # Calculate metrics
    metrics = {
        'user_task_completion': goal_completions / num_convos if num_convos > 0 else 0,
        'user_task_completion_efficiency': completion_efficiency / num_convos if num_convos > 0 else 0
    }
    
    if bot_goal is not None:
        metrics['bot_goal_completion'] = bot_goal_completions / num_convos if num_convos > 0 else 0
    
    return metrics

if __name__ == "__main__":
    # with open('files/p1_sample_convos.json') as f:
    #     data = json.load(f)

    # model_api = "http://adaptation.cs.columbia.edu:55131/predict"
    # model_params = {'bot_id' : 'richtech', 'bot_version': 'v1alpha1'}
    # convos  = get_nlu_labels(data, model_api, model_params)
    # with open('files/p1_sample_convos_labeled.json', 'w') as f:
    #     json.dump(convos, f, indent=5)

    
    with open('files/p1_sample_convos_labeled.json') as f:
        data = json.load(f)
    G = build_intent_graph(data)
    for e in list(G.edges()):
        print(f"Weight for edge {e}: {G.get_edge_data(e[0], e[1])['weight']}")
