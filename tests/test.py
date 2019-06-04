from custom_components.leuven_template.sensor import process_xml

if __name__ == "__main__":
    with open('./tests/data.xml') as fin:
        data = fin.read()
        print(data)

        output = process_xml(data)

        print(output)