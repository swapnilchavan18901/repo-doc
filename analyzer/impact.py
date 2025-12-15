def analyze_impact(old_structure, new_structure):
    impact = {
        "added": [],
        "removed": [],
        "modified": []
    }

    old_funcs = set(old_structure.get("functions", []))
    new_funcs = set(new_structure.get("functions", []))

    impact["added"] = list(new_funcs - old_funcs)
    impact["removed"] = list(old_funcs - new_funcs)

    if old_funcs & new_funcs:
        impact["modified"].extend(list(old_funcs & new_funcs))

    return impact
