from compiler import lexemes, semantics, yaml_augmentation, repo_processor, runtime_variables, processor_config_schemas
import argparse
from ruamel.yaml import YAML


# fetch repos, add include statement for the downloaded default_values.yaml
# INPUT: raw site-level-config file filled by site admin
# PROCESS: extract repo_urls, download and save default files for repositories
# OUTPUT: include statements for default files of repositories + raw site level-config file
def phase_1(site_level_configuration_file, main_default_values_file):
    # fetch repo and get default_values.yaml
    repo_urls = lexemes.get_repo_list(site_level_configuration_file)
    print(repo_urls)
    file_names_repository_default = [main_default_values_file]
    for url in repo_urls:
        file_names_repository_default.append(repo_processor.get_default_values(url))

    default_includes_yaml_file = yaml_augmentation.add_include_statements_for_default_files(file_names_repository_default, site_level_configuration_file)
    return default_includes_yaml_file, repo_urls


# add data from all includes
# INPUT: include statements for default files of repositories + raw site level-config file
# PROCESS: recursively replace include statements with contents of the files that are to be included.
# OUTPUT: include statements replaced by contents of referred files + raw site-level-config file
def phase_2(default_includes_yaml_file):
    return yaml_augmentation.add_included_files(default_includes_yaml_file)


def phase_3(include_made):
    runtime_vars, config_file = runtime_variables.extract_runtime_variables(include_made)
    return runtime_vars, runtime_variables.add_runtime_variables(runtime_vars, config_file)


# syntax_checking
def phase_4(final_yaml_file):
    return semantics.check_yaml_syntax(final_yaml_file)


def phase_5(phase_4_output, runtime_vars):
    phase_4_output_file = open(phase_4_output.name, 'r')
    data = yaml.load(phase_4_output_file)
    output = {}
    for data_section in data:
        if data_section == 'lightweight_components':
            updated_components = []
            for lightweight_component in data[data_section]:
                print "Component: " + lightweight_component['name']
                updated_component = {}
                for component_section in lightweight_component:
                    if component_section == 'config':
                        repo_url = lightweight_component['repository_url']
                        repo_processor.get_config_schema(repo_url)
                        repo_processor.get_meta_info(repo_url)
                        repo_info = repo_processor.analyse_repo_url(repo_url)
                        config_schema_file_name = repo_processor.generate_config_schema_file_name(repo_info)
                        config_schema_file = open(config_schema_file_name, 'r')
                        meta_info_file_name = repo_processor.generate_meta_info_file_name(repo_info)
                        meta_info_file = open(meta_info_file_name, 'r')
                        default_data_file_name = repo_processor.generate_default_file_name(repo_info)
                        default_data_runtime_file = open(default_data_file_name + ".runtime", 'w')
                        default_data_file = open(default_data_file_name, 'r')
                        default_data_runtime_file.write(runtime_vars)
                        for l in default_data_file.readlines():
                            default_data_runtime_file.write(l)
                        default_data_file.close()
                        default_data_runtime_file.close()
                        config_schema_file.close()
                        meta_info_file.close()
                        augmented_config = processor_config_schemas.process_config_schema(lightweight_component[component_section], config_schema_file, default_data_runtime_file, meta_info_file)
                        updated_component[component_section] = augmented_config
                    else:
                        updated_component[component_section] = lightweight_component[component_section]
                updated_components.append(updated_component)
            output[data_section] = updated_components
        else:
            output[data_section] = data[data_section]
    print output
    return output
def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    return {
        'site_level_configuration_file': args.filename,
        'output': args.output
    }

if __name__ == "__main__":

    args = parse_args()
    site_level_configuration_file = open(args['site_level_configuration_file'], 'r')
    main_default_values_file = "./tests/resources/default_values.yaml"
    output = open(args['output'], 'w')
    yaml = YAML()
    phase_1_output, repo_urls = phase_1(site_level_configuration_file, main_default_values_file)
    phase_2_output = phase_2(phase_1_output)
    runtime_vars, phase_3_output = phase_3(phase_2_output)
    phase_4_output = phase_4(phase_3_output)
    # augmented_yaml_file = phase_3(open('./.temp/runtime.yaml', 'r'), output)
    augmented_yaml_file = open(phase_4_output.name, 'r')
    # data =yaml.load(augmented_yaml_file)
    # print data['lightweight_components'][0]['config']['cream-info']['ce_cpu_model']
    # print data['supported_virtual_organizations']
    # print data['site']['latitude']
    phase_5_output = phase_5(phase_4_output, runtime_vars)
    yaml.dump(phase_5_output, output)
    output.close()
