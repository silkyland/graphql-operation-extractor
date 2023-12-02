import re


class GraphQLOperationExtractor:
    def __init__(self, schema_file_path: str, output_file_path: str, **kwargs: dict[str, str]) -> None:
        self.schema = self.read_file(schema_file_path)
        self.output_file_path = output_file_path
        self.fragment_suffix = kwargs.get("fragment_suffix", "Fragment")
        self.query_suffix = kwargs.get("query_suffix", "Query")
        self.mutation_suffix = kwargs.get("mutation_suffix", "Mutation")
        self.subscription_suffix = kwargs.get(
            "subscription_suffix", "Subscription")
        self.add_typename = kwargs.get("add_typename", False)

        self.query_template = "query {query_name}{query_suffix}{params}{{{query_name}{params_inside} {maybe_fragment_name}}}"
        self.mutation_template = "mutation {query_name}{mutation_suffix}{params} {{{query_name}{params_inside} {maybe_fragment_name}}}"
        self.subscription_template = "subscription {query_name}{subscription_suffix}{params} {{{query_name}{params_inside} {maybe_fragment_name}}}"
        self.fragment_template = "fragment {fragment_name}{fragment_suffix} on {type_name} {{{fields}}}"
        self.fragments = []
        self.fragment_mapping = self.get_fragment_name()

    def get_fragment_name(self) -> dict:
        fragment_mapping = {}
        type_pattern = r"type (\w+)( implements Node)? \{(.*?)\}"
        union_pattern = r"union (\w+) = (.*)"
        type_matches = re.findall(type_pattern, self.schema, flags=re.DOTALL)
        union_matches = re.findall(union_pattern, self.schema)
        for type_name, _, fields in type_matches:
            if type_name not in ("Query", "Mutation", "Subscription"):
                field_names = [
                    line.split(":")[0].strip() for line in fields.strip().split("\n")
                ]
                fragment_name = f"{type_name}Fragment"
                fragment = self.fragment_template.format(
                    fragment_name=fragment_name,
                    fragment_suffix=self.fragment_suffix,
                    type_name=type_name,
                    fields=" ".join(field_names),
                )
                self.fragments.append(fragment)
                fragment_mapping[type_name] = fragment_name

        for union_name, _ in union_matches:
            fragment_mapping[union_name] = f"{union_name}Fragment"

        return fragment_mapping

    def extract_fragments_from_schema(self) -> list:
        fragments = []
        type_pattern = r"type (\w+)( implements Node)? \{(.*?)\}"
        interface_pattern = r"interface (\w+) \{(.*?)\}"
        union_pattern = r"union (\w+) = (.*)"
        type_matches = re.findall(type_pattern, self.schema, flags=re.DOTALL)

        # Process types and interfaces
        for type_name, _, fields in type_matches:
            if type_name not in ("Query", "Mutation", "Subscription"):
                fragment_fields = self.process_fields(fields)
                fragment = self.fragment_template.format(
                    fragment_name=f"{type_name}",
                    fragment_suffix=self.fragment_suffix,
                    type_name=type_name,
                    fields="\n  ".join(fragment_fields),
                )
                fragments.append(fragment)

        interface_matches = re.findall(
            interface_pattern, self.schema, flags=re.DOTALL)
        for interface_name, fields in interface_matches:
            fragment_fields = self.process_fields(fields)
            fragment = self.fragment_template.format(
                fragment_name=f"{interface_name}",
                fragment_suffix=self.fragment_suffix,
                type_name=interface_name,
                fields="\n  ".join(fragment_fields),
            )
            fragments.append(fragment)

        # Process unions
        union_matches = re.findall(union_pattern, self.schema)
        for union_name, union_members in union_matches:
            members = union_members.split("|")
            member_fragments = [
                f"... on {member.strip()} {{\n    ...{self.fragment_mapping.get(member.strip(), member.strip() + self.fragment_suffix)}\n  }}"
                for member in members
            ]
            union_fragment = self.fragment_template.format(
                fragment_name=f"{union_name}",
                fragment_suffix=self.fragment_suffix,
                type_name=union_name,
                fields="\n".join(member_fragments),
            )
            fragments.append(union_fragment)

        return fragments

    def process_fields(self, fields: str) -> list:
        field_lines = fields.strip().split("\n")
        processed_fields = []
        for line in field_lines:
            field_name, field_type = (
                line.split(":")[0].strip(),
                line.split(":")[1].strip(),
            )
            normalized_type = re.sub(r'[\[\]!]', '', field_type)
            if normalized_type in self.fragment_mapping:
                print({self.fragment_mapping[normalized_type]})
                formated = f"{field_name} {{\n    ...{self.fragment_mapping[normalized_type]}\n  }}"
                processed_fields.append(formated)
            else:
                processed_fields.append(field_name)
        return processed_fields

    def extract_queries_from_schema(self) -> list:
        queries = []
        query_pattern = r"type Query \{(.*?)\}"
        field_pattern = r"(\w+)(\(.*?\))?: (\w+|\[.*?\])"

        query_matches = re.findall(query_pattern, self.schema, flags=re.DOTALL)
        if query_matches:
            query_fields = query_matches[0]
            field_matches = re.findall(
                field_pattern, query_fields, flags=re.DOTALL)
            for query_name, params, return_type in field_matches:
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(
                    re.sub(r'[\[\]!]', '', return_type), "")
                query = self.query_template.format(
                    query_name=query_name,
                    query_suffix=self.query_suffix,
                    params=formatted_params,
                    params_inside=params_inside,
                    maybe_fragment_name="{..." +
                    fragment_name+"}" if fragment_name else ""
                )
                queries.append(query)
        return queries

    def extract_mutations_from_schema(self) -> list:
        mutations = []
        mutation_pattern = r"type Mutation \{(.*?)\}"
        field_pattern = r"(\w+)(\(.*?\))?: (\w+|\[.*?\])"

        mutation_matches = re.findall(
            mutation_pattern, self.schema, flags=re.DOTALL)
        if mutation_matches:
            mutation_fields = mutation_matches[0]
            field_matches = re.findall(
                field_pattern, mutation_fields, flags=re.DOTALL)
            for mutation_name, params, return_type in field_matches:
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(
                    re.sub(r'[\[\]!]', '', return_type), "")
                mutation = self.mutation_template.format(
                    query_name=mutation_name,
                    mutation_suffix=self.mutation_suffix,
                    params=formatted_params,
                    params_inside=params_inside,
                    maybe_fragment_name="{..." +
                    fragment_name+"}" if fragment_name else ""
                )
                mutations.append(mutation)
        return mutations

    def extract_subscriptions_from_schema(self) -> list:
        subscriptions = []
        subscription_pattern = r"type Subscription \{(.*?)\}"
        field_pattern = r"(\w+)(\(.*?\))?: (\w+|\[.*?\])"

        subscription_matches = re.findall(
            subscription_pattern, self.schema, flags=re.DOTALL)
        if subscription_matches:
            subscription_fields = subscription_matches[0]
            field_matches = re.findall(
                field_pattern, subscription_fields, flags=re.DOTALL)
            for subscription_name, params, return_type in field_matches:
                formatted_params, params_inside = self.process_params(params)
                fragment_name = self.fragment_mapping.get(
                    re.sub(r'[\[\]!]', '', return_type), "")
                subscription = self.subscription_template.format(
                    query_name=subscription_name,
                    subscription_suffix=self.subscription_suffix,
                    params=formatted_params,
                    params_inside=params_inside,
                    maybe_fragment_name="{..." +
                    fragment_name+"}" if fragment_name else "",
                )
                subscriptions.append(subscription)
        return subscriptions

    def process_params(self, params: str) -> (str, str):
        if params:
            # Splitting parameters and adding types
            param_names = params[1:-1].split(",")
            formatted_params = (
                "(" + ", ".join([f"${p.strip()}" for p in param_names]) + ")"
            )
            params_inside = (
                "("
                + ", ".join(
                    [
                        f"{p.split(':')[0].strip()}: ${p.split(':')[0].strip()}"
                        for p in param_names
                    ]
                )
                + ")"
            )
            return formatted_params, params_inside
        return "", ""

    def read_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            return file.read()

    def write_file(self, file_path: str, content: str) -> None:
        with open(file_path, "w") as file:
            file.write(content)

    def extract(self) -> None:
        queries = self.extract_queries_from_schema()
        fragments = self.extract_fragments_from_schema()
        mutations = self.extract_mutations_from_schema()
        subscriptions = self.extract_subscriptions_from_schema()
        self.write_file(self.output_file_path,
                        "\n\n".join(fragments + queries + mutations + subscriptions))

    def run(self) -> None:
        self.extract()
        print("Done!")


if __name__ == "__main__":
    schema_file_path = "input/schema.gql"
    output_file_path = "output/" + \
        schema_file_path.split("/")[-1].split(".")[0] + ".extracted.gql"
    extractor = GraphQLOperationExtractor(
        schema_file_path, output_file_path, query_suffix="", mutation_suffix="", subscription_suffix="")
    extractor.run()
