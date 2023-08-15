
import json
import os
import argparse

def identify_api_document(content):
    """
    Identify the type of the API documentation based on its content.
    """
    if "swagger" in content:
        return "swagger"
    elif "info" in content and "item" in content:
        return "postman"
    else:
        return "unknown"
    
def analyze_api_file(file_path):
    """
    Analyze a given API documentation file and return details about it.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    if "swagger" in content:
        return refined_parse_swagger_content(content)
    elif "info" in content and "item" in content:
        return refined_parse_postman_content(content)
    else:
        return None
    
def analyze_directory(directory):
    results = {}
    errors = []

    for file in os.listdir(directory):
        if file.endswith('.json') or file.endswith('.yaml') or file.endswith('.yml'):
            try:
                content = None
                if file.endswith('.json'):
                    with open(os.path.join(directory, file), 'r', encoding='utf-8', errors='replace') as f:
                        content = json.load(f)
                elif file.endswith('.yaml') or file.endswith('.yml'):
                    with open(os.path.join(directory, file), 'r', encoding='utf-8', errors='replace') as f:
                        content = yaml.safe_load(f)
                
                doc_type = identify_api_document(content)
                
                if doc_type == "postman":
                    details = refined_parse_postman_content(content)
                elif doc_type == "swagger":
                    details = refined_parse_swagger_content(content)
                else:
                    details = {"message": "Unknown API documentation type."}
                results[file] = details
            except Exception as e:
                errors.append((file, str(e)))

    return results, errors


def refined_parse_postman_content(content):
    """
    Parse the content of a Postman collection to extract relevant details.
    """
    # Initialize result details
    details = {
        "Total Requests/Endpoints": 0,
        "HTTP Methods Distribution": {
            "GET": 0,
            "POST": 0,
            "PUT": 0,
            "DELETE": 0,
            "PATCH": 0,
            "HEAD": 0,
            "OPTIONS": 0,
            "UNKNOWN": 0
        },
        "Total Parameters": 0
    }
    
    # Extract requests
    requests = extract_postman_items(content['item'])
    
    # Populate details
    details["Total Requests/Endpoints"] = len(requests)
    
    for request in requests:
        if isinstance(request, dict) and 'method' in request:
            method = request['method'].upper()
            details["HTTP Methods Distribution"][method] = details["HTTP Methods Distribution"].get(method, 0) + 1
            if 'url' in request and isinstance(request['url'], dict) and 'query' in request['url']:
                details["Total Parameters"] += len(request['url']['query'])

    return details

def refined_parse_swagger_content(content):
    if not isinstance(content, dict):
        return {
            "Total Requests/Endpoints": 0,
            "HTTP Methods Distribution": {},
            "Total Parameters": 0
        }

    endpoints = []
    methods_distribution = {
        "GET": 0,
        "POST": 0,
        "PUT": 0,
        "DELETE": 0,
        "PATCH": 0,
        "OPTIONS": 0,
        "HEAD": 0,
        "UNKNOWN": 0
    }
    total_parameters = 0

    paths = content.get("paths", {})
    if not isinstance(paths, dict):  # Ensure that paths is a dictionary
        paths = {}
    for path, info in paths.items():
        if not isinstance(info, dict):  # Ensure that each path info is a dictionary
            continue
        endpoints.append(path)
        for method, details in info.items():
            if not isinstance(details, dict):  # Ensure that details for each method is a dictionary
                continue
            methods_distribution[method.upper()] = methods_distribution.get(method.upper(), 0) + 1
            parameters = details.get("parameters", [])
            total_parameters += len(parameters)

    return {
        "Total Requests/Endpoints": len(endpoints),
        "HTTP Methods Distribution": methods_distribution,
        "Total Parameters": total_parameters
    }


def extract_postman_items(items_list):
    """
    Recursively extract requests from a nested Postman items list.
    """
    requests = []
    for item in items_list:
        if 'request' in item:
            requests.append(item['request'])
        if 'item' in item:
            requests.extend(extract_postman_items(item['item']))
    return requests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze API documentation files.')
    parser.add_argument('-d', '--directory', required=True, help='Directory containing API documentation files.')
    args = parser.parse_args()

    results, errors = analyze_directory(args.directory)
    for file_name, details in results.items():
        print("\nProcessing results for:", file_name)
        print("-" * 30)
        print("Total Requests/Endpoints:", details['Total Requests/Endpoints'])
        print("HTTP Methods Distribution:", {method: count for method, count in details['HTTP Methods Distribution'].items() if count > 0})
        print("Total Parameters:", details['Total Parameters'])
        print("-" * 30)

    if errors:
        print("\nErrors encountered for the following files:")
        for file_name, error_msg in errors:
            print(file_name, "- Error:", error_msg)
