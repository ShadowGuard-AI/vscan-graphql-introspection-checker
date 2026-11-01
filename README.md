# vscan-graphql-introspection-checker
Checks for enabled GraphQL introspection, potentially revealing the API's schema and enabling malicious queries. - Focused on Lightweight web application vulnerability scanning focused on identifying common misconfigurations and publicly known vulnerabilities

## Install
`git clone https://github.com/ShadowGuardAI/vscan-graphql-introspection-checker`

## Usage
`./vscan-graphql-introspection-checker [params]`

Without `-p`, the check sends a GET request with the introspection query as parameters first, and falls back to a POST request when the GET response is HTML. With `-p`, the check sends only a POST request.

A connection failure, an HTTP error status, or a non JSON response is a failed check: the tool prints a FAILED line and exits 1. The DISABLED line at exit 0 is printed only for a well formed JSON response that shows introspection is not enabled.

## Parameters
- `-h`: Show help message and exit
- `-H`: Add custom headers to the request.  Example: -H 
- `-p`: Force POST request

## License
Copyright (c) ShadowGuardAI
