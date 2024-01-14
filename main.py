import re
from typing import Dict, Tuple, List, Optional

class GraphQLOperationExtractor:
    def __init__(self, schema_file_path: str, output_file_path: str, options: Dict = None):
        if options is None:
            options = {}
        with open(schema_file_path, 'r') as file:
            raw_schema = file.read()
        self.schema = self.preprocess_schema(raw_schema)
        self.output_file_path = output_file_path
        self.fragment_suffix = options.get('fragmentSuffix', 'Fragment')
        self.query_suffix = options.get('querySuffix', '')
        self.mutation_suffix = options.get('mutationSuffix', '')
        self.subscription_suffix = options.get('subscriptionSuffix', '')
        self.add_typename = options.get('addTypename', False)
        self.query_template = "query {queryName}{querySuffix}{params}{{queryName}{paramsInside} {maybeFragmentName} \n }}"
        self.mutation_template = "mutation {queryName}{mutationSuffix}{params}{{queryName}{paramsInside} {maybeFragmentName} \n }}"
        self.subscription_template = "subscription {queryName}{subscriptionSuffix}{params}{{queryName}{paramsInside} {maybeFragmentName} \n }}"
        self.fragment_template = "fragment {fragmentName}{fragmentSuffix} on {typeName} {{fields} \n }}"
        self.fragments = []
        self.fragment_mapping = self.get_fragment_name()

    def get_fragment_name(self) -> Dict[str, str]:
        fragment_mapping = {}
        type_pattern = re.compile(r'type (\w+)( implements Node)? {(.*?)}', re.DOTALL)
        union_pattern = re.compile(r'union (\w+) = (.*)')

        type_matches = type_pattern.findall(self.schema)
        for typeName, _, fields in type_matches:
            if typeName not in ["Query", "Mutation", "Subscription"]:
                fragment_name = f'{typeName}{self.fragment_suffix}'
                fragment_mapping[typeName] = fragment_name

        union_matches = union_pattern.findall(self.schema)
        for unionName, _ in union_matches:
            fragment_mapping[unionName] = f'{unionName}{self.fragment_suffix}'

        return fragment_mapping

    def process_fields(self, fields: str) -> List[str]:
        processed_fields = []
        for line in fields.strip().split('\n'):
            field, fieldType = map(str.strip, line.split(':'))
            normalizedType = re.sub(r'[\[\]!]', '', fieldType)
            if normalizedType in self.fragment_mapping:
                formatted = f'# {field} {{\n  #   ...{self.fragment_mapping[normalizedType]}\n  # }}'
                processed_fields.append(formatted)
            else:
                processed_fields.append(field)
        return processed_fields

    def extract_fragments_from_schema(self) -> List[str]:
        fragments = []
        type_pattern = re.compile(r'type (\w+)( implements Node)? {(.*?)}', re.DOTALL)
        interface_pattern = re.compile(r'interface (\w+) {(.*?)}', re.DOTALL)
        union_pattern = re.compile(r'union (\w+) = (.*)')

        type_matches = type_pattern.findall(self.schema)
        for typeName, _, fields in type_matches:
            if typeName not in ["Query", "Mutation", "Subscription"]:
                fragment_fields = self.process_fields(fields)
                fragment = self.fragment_template.format(
                    fragmentName=typeName, 
                    fragmentSuffix=self.fragment_suffix, 
                    typeName=typeName, 
                    fields='\n  '.join(fragment_fields))
                fragments.append(fragment)

        interface_matches = interface_pattern.findall(self.schema)
        for interfaceName, fields in interface_matches:
            fragment_fields = self.process_fields(fields)
            fragment = self.fragment_template.format(
                    fragmentName=interfaceName, 
                    fragmentSuffix=self.fragment_suffix, 
                    typeName=interfaceName, 
                    fields='\n  '.join(fragment_fields))
            fragments.append(fragment)

        union_matches = union_pattern.findall(self.schema)
        for unionName, _ in union_matches:
            fragment_mapping = self.fragment_mapping.get(unionName, f'{unionName}{self.fragment_suffix}')
            fragment = self.fragment_template.format(
                    fragmentName=unionName, 
                    fragmentSuffix=self.fragment_suffix, 
                    typeName=unionName, 
                    fields=fragment_mapping)
            fragments.append(fragment)

        return fragments
        
    def extract_queries_from_schema(self) -> List[str]:
        queries = []
        query_pattern = re.compile(r'type Query {(.*?)}', re.DOTALL)
        field_pattern = re.compile(r'(\w+)(\(.*?\))?: (\w+|\[.*?\])')

        query_matches = query_pattern.findall(self.schema)
        for query_fields in query_matches:
            for queryName, params, returnType in field_pattern.findall(query_fields):
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(re.sub(r'[\[\]!]', '', returnType), "")
                query = self.query_template.format(
                    queryName=queryName,
                    querySuffix=self.query_suffix,
                    params=formatted_params,
                    paramsInside=params_inside,
                    maybeFragmentName=f'{{\n  ...{fragment_name}\n}}' if fragment_name else ""
                )
                queries.append(query)
        return queries

    def extract_mutations_from_schema(self) -> List[str]:
        mutations = []
        mutation_pattern = re.compile(r'type Mutation {(.*?)}', re.DOTALL)
        field_pattern = re.compile(r'(\w+)(\(.*?\))?: (\w+|\[.*?\])')

        mutation_matches = mutation_pattern.findall(self.schema)
        for mutation_fields in mutation_matches:
            for mutationName, params, returnType in field_pattern.findall(mutation_fields):
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(re.sub(r'[\[\]!]', '', returnType), "")
                mutation = self.mutation_template.format(
                    queryName=mutationName,
                    mutationSuffix=self.mutation_suffix,
                    params=formatted_params,
                    paramsInside=params_inside,
                    maybeFragmentName=f'{{\n  ...{fragment_name}\n}}' if fragment_name else ""
                )
                mutations.append(mutation)
        return mutations

    def extract_subscriptions_from_schema(self) -> List[str]:
        subscriptions = []
        subscription_pattern = re.compile(r'type Subscription {(.*?)}', re.DOTALL)
        field_pattern = re.compile(r'(\w+)(\(.*?\))?: (\w+|\[.*?\])')

        subscription_matches = subscription_pattern.findall(self.schema)
        for subscription_fields in subscription_matches:
            for subscriptionName, params, returnType in field_pattern.findall(subscription_fields):
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(re.sub(r'[\[\]!]', '', returnType), "")
                subscription = self.subscription_template.format(
                    queryName=subscriptionName,
                    subscriptionSuffix=self.subscription_suffix,
                    params=formatted_params,
                    paramsInside=params_inside,
                    maybeFragmentName=f'{{\n  ...{fragment_name}\n}}' if fragment_name else ""
                )
                subscriptions.append(subscription)
        return subscriptions

    def process_params(self, params: str) -> Tuple[str, str]:
        if params:
            normalized_params = re.sub(r'\s*\n\s*', ' ', params).strip()
            normalized_params = re.sub(r'(\w+!)\s+(\w+)', r'\1, \2', normalized_params)
            param_names = [param.strip() for param in normalized_params[1:-1].split(',')]
            formatted_params = ', '.join([f'${param}' for param in param_names])
            params_inside = ', '.join([f'{param.split(":")[0].strip()}: ${param.split(":")[0].strip()}' for param in param_names])
            return f'({formatted_params})', f'({params_inside})'
        return '', ''

    def extract(self) -> None:
        queries = self.extract_queries_from_schema()
        fragments = self.extract_fragments_from_schema()
        mutations = self.extract_mutations_from_schema()
        subscriptions = self.extract_subscriptions_from_schema()
        with open(self.output_file_path, 'w') as file:
            file.write('\n\n'.join(fragments + queries + mutations + subscriptions))

    def run(self) -> None:
        self.extract()
        print("Done!")

schema_file_path = "./graphql/schema.graphql"
output_file_path = "graphql/output/operation.graphql"

extractor = GraphQLOperationExtractor(schema_file_path, output_file_path, {
    'fragmentSuffix': "",
    'querySuffix': "",
    'mutationSuffix': "",
    'subscriptionSuffix': "",
    'addTypename': False,
})

extractor.run()
