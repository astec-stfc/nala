import os
import yaml

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/types/type_conversion_rules.yaml",
    "r",
) as infile:
    type_conversion_rules = yaml.safe_load(infile)
    type_conversion_rules_Elegant = type_conversion_rules["elegant"]
    type_conversion_rules_Genesis = type_conversion_rules["genesis"]
    type_conversion_rules_Opal = type_conversion_rules["opal"]
    type_conversion_rules_Names = type_conversion_rules["name"]
    type_conversion_rules_aliases = type_conversion_rules["aliases"]["elegant"]

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_elegant.yaml",
    "r",
) as infile:
    keyword_conversion_rules_elegant = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/elements_elegant.yaml",
    "r",
) as infile:
    elements_Elegant = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_ocelot.yaml",
    "r",
) as infile:
    keyword_conversion_rules_ocelot = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/elements_ocelot.yaml",
    "r",
) as infile:
    elements_Ocelot = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_cheetah.yaml",
    "r",
) as infile:
    keyword_conversion_rules_cheetah = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/elements_cheetah.yaml",
    "r",
) as infile:
    elements_Cheetah = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/elements_opal.yaml",
    "r",
) as infile:
    elements_Opal = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_opal.yaml",
    "r",
) as infile:
    keyword_conversion_rules_opal = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_Xsuite.yaml",
    "r",
) as infile:
    keyword_conversion_rules_xsuite = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_wake_t.yaml",
    "r",
) as infile:
    keyword_conversion_rules_wake_t = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/keywords/keyword_conversion_rules_genesis.yaml",
    "r",
) as infile:
    keyword_conversion_rules_genesis = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/elements_genesis.yaml",
    "r",
) as infile:
    elements_Genesis = yaml.safe_load(infile)

with open(
    os.path.dirname(os.path.abspath(__file__)) + "/../conversion_rules/elements/element_keywords.yaml",
    "r",
) as infile:
    element_keywords = yaml.safe_load(infile)