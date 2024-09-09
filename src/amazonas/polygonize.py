import rasterio.features
import scipy
import scipy.ndimage
import shapely.geometry
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import rasterio as rio


def threshold_and_polygonize(pop, smod, transform, pop_thresh=0, smod_thresh=11):
    if smod_thresh <= 10:
        warnings.warn("El threshold de SMOD es menor o igual a 10. Esto causará que píxeles correspondientes a agua se incluyan en el análisis.")
    
    masks = [
        pop >= pop_thresh,
        ~np.isnan(pop),
        smod >= smod_thresh,
    ]
    mask = np.ones(smod.shape, dtype=bool)
    for m in masks:
        mask &= m

    smod_filtered = np.where(mask, smod, 0)
    smod_filtered = smod_filtered > 0
    smod_components, _ = scipy.ndimage.label(smod_filtered, structure=scipy.ndimage.generate_binary_structure(2, 2))
    feature_geometries = rio.features.shapes(smod_components, connectivity=8, transform=transform)

    pop_temp = pop.copy()
    pop_temp[np.isnan(pop_temp)] = 0
    pop_temp = pop_temp.reshape(-1)

    counts = np.bincount(smod_components.reshape(-1), weights=pop_temp)

    df_out = []
    for geom, value in feature_geometries:
        if value != 0:
            df_out.append(dict(
                pop=counts[int(value)],
                geometry=shapely.geometry.shape(geom)
            ))
    df_out = gpd.GeoDataFrame(df_out, crs="ESRI:54009")
    
    return df_out


def join_nearby(polygons, buffer=1000):
    buffered = gpd.GeoDataFrame(index=polygons.index, geometry=polygons.buffer(buffer, join_style="round"), crs=polygons.crs)

    buffer_joins = buffered.sjoin(buffered, how="inner", predicate="intersects")
    grouped = buffer_joins.groupby(level=0)["index_right"].apply(list)

    g = nx.Graph()
    for source, dests in grouped.items():
        g.add_node(source)
        for dest in dests:
            if source != dest:
                g.add_edge(source, dest)

    polygons_labeled = polygons.copy()
    for i, indices in enumerate(nx.connected_components(g)):
        for idx in indices:
            polygons_labeled.loc[idx, "label"] = i
    polygons_labeled["label"] = polygons_labeled["label"].astype(int)

    polygons_labeled = polygons_labeled.dissolve(by="label", aggfunc="sum")
    return polygons_labeled