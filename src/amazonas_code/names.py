def process_features(features, gadm, *, wanted_places):
    wanted_features = features.copy()

    wanted_features = wanted_features[wanted_features["element_type"] == "node"]

    wanted_features = features[features["place"].isin(wanted_places)]

    wanted_features = wanted_features.dropna(subset=["name"])
    wanted_features["name"] = wanted_features["name"].str.casefold().str.strip()

    print(len(wanted_features))
    wanted_features = wanted_features.sjoin(gadm, how="inner", predicate="within")
    print(len(wanted_features))
    wanted_features["name_combined"] = wanted_features["name"] + "+" + wanted_features["place"] + "+" + wanted_features["GID"]

    wanted_features = wanted_features[["name_combined", "geometry"]]
    wanted_features = wanted_features.to_crs("ESRI:54009")
    return wanted_features


def join_and_get_names(polygons, features, buffer=0):
    polygons = polygons.copy()
    polygons["geometry"] = polygons.buffer(buffer)
    joined = polygons.sjoin(features, how="inner", predicate="contains")
    names = joined.groupby(level=0)["name_combined"].apply("\t".join)
    return names