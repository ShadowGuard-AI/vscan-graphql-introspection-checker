import argparse
import requests
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define GraphQL introspection query
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
          }
        }
      }
    }
  }
}
"""


def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Checks for enabled GraphQL introspection.")
    parser.add_argument("url", help="The URL of the GraphQL endpoint to check.")
    parser.add_argument("-H", "--header", action='append', default=[],
                        help="Add custom headers to the request.  Example: -H 'Authorization: Bearer <token>'")
    parser.add_argument("-p", "--post", action="store_true", help="Force POST request (default without this flag: try a GET request first)")
    return parser


def is_html(response):
    """
    Checks if the response is HTML.
    """
    content_type = response.headers.get('Content-Type', '').lower()
    return 'text/html' in content_type

def check_introspection(url, headers, use_post=False):
    """
    Checks if GraphQL introspection is enabled at the given URL.

    Args:
        url (str): The URL of the GraphQL endpoint.
        headers (dict): A dictionary of headers to include in the request.
        use_post (bool): A boolean to force the use of POST requests.

    Returns:
        bool or None: True if introspection is enabled, False only for a
        well formed JSON response showing introspection disabled, and
        None when the check failed (connection failure, HTTP error, or
        a non JSON response), which is not a verdict about the target.
    """
    try:
        payload = {'query': INTROSPECTION_QUERY}

        if use_post:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        else:
            response = requests.get(url, params=payload, headers=headers, timeout=10)
            #Check if it is HTML
            if is_html(response):
                #Attempt POST Request as a fallback
                logging.info("Received HTML response to the GET request, attempting a POST request.")
                response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code >= 400:
            logging.error(f"Check failed: HTTP status {response.status_code}.")
            return None

        content_type = response.headers.get('Content-Type', '').lower()

        if 'application/json' not in content_type:
            logging.error(f"Check failed: unexpected content type: {content_type}. Expected application/json.")
            return None

        try:
            data = response.json()
        except ValueError:
            logging.error("Check failed: response was not valid JSON.")
            return None

        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict) and '__schema' in data['data']:
            logging.info("GraphQL introspection is enabled.")
            return True
        if isinstance(data, dict):
            logging.info("GraphQL introspection is not enabled or schema is restricted.")
            return False
        logging.error("Check failed: JSON response was not an object.")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


def parse_headers(header_list):
    """Parses a list of header strings into a dictionary."""
    headers = {}
    for header_str in header_list:
        try:
            key, value = header_str.split(":", 1)
            headers[key.strip()] = value.strip()
        except ValueError:
            logging.error(f"Invalid header format: {header_str}.  Expected 'Key: Value'")
    return headers


def main():
    """
    Main function to execute the GraphQL introspection check.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    url = args.url
    headers = parse_headers(args.header)
    use_post = args.post

    # Input validation
    if not url:
        logging.error("URL is required.")
        sys.exit(1)

    # Security best practices: Sanitize URL (basic example, consider stronger methods)
    if not url.startswith(('http://', 'https://')):
        logging.warning("URL does not start with http:// or https://.  Assuming https://")
        url = 'https://' + url

    logging.info(f"Checking GraphQL introspection at: {url}")

    result = check_introspection(url, headers, use_post)
    if result is None:
        print("GraphQL introspection check FAILED: the endpoint could not be assessed.")
        sys.exit(1)
    if result:
        print("GraphQL introspection is ENABLED.")
    else:
        print("GraphQL introspection is DISABLED or restricted.")


if __name__ == "__main__":
    main()

# Example Usage:
# python main.py https://example.com/graphql
# python main.py https://example.com/graphql -H "Authorization: Bearer <token>"
# python main.py https://example.com/graphql --post
# python main.py https://example.com/graphql -H "Content-Type: application/json" -H "X-Custom-Header: value"