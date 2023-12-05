# GraphQLOperationExtractor

The GraphQLOperationExtractor is a Python project aimed at simplifying the work of developers who use GraphQL. It automatically extracts GraphQL operations such as queries, mutations, and subscriptions, as well as fragments from a GraphQL schema file. This tool is invaluable in reducing the time and effort required in manually generating operation templates from a schema, thereby minimizing potential errors.

[![by me a coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/silkyland)

## Features

- Extracts GraphQL operations: queries, mutations, and subscriptions from a schema file.
- Extracts GraphQL fragments from a schema file.
- Allows customization of operation and fragment suffixes.
- Supports adding typenames to extracted operations.
- Outputs the extracted operations and fragments to a specified file.

## How to Use

1. **Initialize the extractor:** Create an instance of the GraphQLOperationExtractor class. Provide the path to your GraphQL schema file and the desired output file path. Optional arguments can be provided for customizing suffixes and adding typenames.

   ```python
   extractor = GraphQLOperationExtractor(
       schema_file_path,
       output_file_path,
       query_suffix="",
       mutation_suffix="",
       subscription_suffix=""
   )
   ```

2. **Run the extractor:** Execute the `run` method on the extractor instance to start the extraction process. This will write the operations and fragments to the output file.

   ```python
   extractor.run()
   ```

3. **Check the output:** The extracted operations and fragments will be in the output file specified during initialization.

## Example

In the example below, the extractor is set up with a schema file located at `input/schema.gql`. The output file path is `output/schema.extracted.gql`. After initialization, the extractor runs, writing the extracted data to the output file.

```python
if __name__ == "__main__":
    schema_file_path = "input/schema.gql"
    output_file_path = "output/" + \
        schema_file_path.split("/")[-1].split(".")[0] + ".extracted.gql"
    extractor = GraphQLOperationExtractor(
        schema_file_path,
        output_file_path,
        query_suffix="",
        mutation_suffix="",
        subscription_suffix=""
    )
    extractor.run()
```

## Requirements

- Python 3.6 or later
- `re` module for regular expressions

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](https://choosealicense.com/licenses/mit/)
