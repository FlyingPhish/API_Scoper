import json
import yaml
import os
import argparse

def identify_api_document(content):
    """
    Identify the type of the API documentation based on its content.
    """
    if "swagger" in content or "openapi" in content:
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

    if identify_api_document(content) == "swagger":
        return parse_swagger_content(content)
    elif identify_api_document(content) == "postman":
        return parse_postman_content(content)
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
                    details = parse_postman_content(content)
                elif doc_type == "swagger":
                    details = parse_swagger_content(content)
                else:
                    details = {"message": "Unknown API documentation type."}
                results[file] = details
            except Exception as e:
                errors.append((file, str(e)))

    return results, errors

def parse_postman_content(content):
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

def parse_swagger_content(content):
    """
    Parse the content of a Swagger/OpenAPI document to extract relevant details.
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

    paths = content.get("paths", {})
    for path, path_info in paths.items():
        for method, operation in path_info.items():
            if method.upper() in details["HTTP Methods Distribution"]:
                details["HTTP Methods Distribution"][method.upper()] += 1
                details["Total Requests/Endpoints"] += 1

                # Count parameters
                total_parameters = 0
                if "parameters" in operation:
                    total_parameters += len(operation["parameters"])
                if "requestBody" in operation:
                    total_parameters += count_request_body_parameters(operation["requestBody"])
                details["Total Parameters"] += total_parameters

    return details

def count_request_body_parameters(request_body):
    """
    Recursively count the number of parameters in the request body.
    """
    if "content" in request_body:
        total_parameters = 0
        for content_type, schema in request_body["content"].items():
            if "schema" in schema:
                total_parameters += count_schema_parameters(schema["schema"])
        return total_parameters
    return 0

def count_schema_parameters(schema):
    """
    Recursively count the number of parameters in a schema.
    """
    if "properties" in schema:
        return len(schema["properties"])
    elif "items" in schema:
        if "properties" in schema["items"]:
            return len(schema["items"]["properties"])
        elif "$ref" in schema["items"]:
            return 1  # Assuming a referenced schema counts as one parameter
    return 0

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