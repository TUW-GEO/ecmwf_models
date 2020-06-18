# -*- coding: utf-8 -*-

'''
Module description
'''
# TODO # (+) 

# NOTES # -

import pandas as pd
import xarray as xr
import os
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib import colorbar
import numpy as np
import matplotlib as mpl
import cartopy
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
from parse import parse
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from pygeogrids.grids import BasicGrid
import warnings
from smecv_grid.grid import SMECV_Grid_v042

def is_spherical(projection):
    if projection in [ccrs.Robinson()]:
        return True
    else:
        return False

def add_grid_labels(ax, x0, x1, y0, y1, dx, dy,
                    lft=True, rgt=True, top=True, bot=True, spherical=False,
                    edgle_label_x=False, edge_label_y=True):
    """Add grid line labels manually for projections that aren't supported

    Args:
        ax (geoaxes.GeoAxesSubplot)
        x0 (scalar)
        x1 (scalar)
        y0 (scalar)
        y1 (scalar)
        dx (scalar)
        dy (scalar)
        lft (bool): whether to label the left side
        rgt (bool): whether to label the right side
        top (bool): whether to label the top side
        bot (bool): whether to label the bottom side
        spherical (bool): pad the labels better if a side of ax is spherical
        edgle_label_x (bool): Plot the first and last Lon label
        edge_label_y (bool): Plot the first and last Lat label
    """
    if dx <= 10:
        dtype = float
    else:
        dtype = int

    if dy <= 10:
        dtype = float
    else:
        dtype = int

    lons = np.arange(x0, x1 + dx / 2., dx, dtype=dtype)
    for i, lon in enumerate(lons):
        if not edgle_label_x:
            if i==0 or i==lons.size-1:
                continue
        if top:
            text = ax.text(lon, y1, '{0}$^\circ$\n\n'.format(lon),
                           va='center', ha='center',
                           transform=ccrs.PlateCarree())
        if bot:
            text = ax.text(lon, y0, '\n\n{0}$^\circ$'.format(lon),
                           va='center', ha='center',
                           transform=ccrs.PlateCarree())

    lats = np.arange(y0, y1 + dy / 2., dy, dtype=dtype)
    for i, lat in enumerate(lats):
        if not edge_label_y:
            if i==0 or i==lats.size-1:
                continue
        if spherical:
            if lat == 0:
                va = 'center'
            elif lat > 0:
                va = 'bottom'
            elif lat < 0:
                va = 'top'
        else:
            va = 'center'
        if lft:
            text = ax.text(x0, lat, '{0}$^\circ$  '.format(lat), va=va, ha='right',
                           transform=ccrs.PlateCarree())
        if rgt:
            text = ax.text(x1, lat, '  {0}$^\circ$'.format(lat), va=va, ha='left',
                           transform=ccrs.PlateCarree())


def convert_2d_1d(data, lons, lats, grid=None):
    '''
    Convert a data array into a Data Frame that can be plotted correctly.
    This is basically the same tha the image class does when selecting 1D arrays.

    Parameters
    -------
    data : dict
        Dictionary that contains a variable name as the key sand an array of
        number as the values
        eg, data = {'var1':np.array([data1]), 'var2':np.array([data2])}
    lons : np.array
        Longitudes according to the passed data
    lats : np.array
        Latitudes according to the passed data
    grid : pygeogrids.BasicGrid or None, optional (default: None)
        Grid that is used to convert the lons and lats to GPIs
        If None is passed, we create one with origin in bottom left and Cellsize
        of 5 DEG.
    '''
    if grid is None:
        grid = BasicGrid(lon=lons, lat=lats).to_cell_grid(5.)

    gpis, dist = grid.find_nearest_gpi(lons, lats)

    df = pd.DataFrame(index=list(range(data.size)), data={'lons':lons, 'lats':lats,
                                                          'gpi': gpis, 'dist':dist})
    for k,v in data.items():
        df[k] = data[k].flatten()

    df = df.set_index('gpi').sort_index()

    return df



def cp_map(df, col, grid=None, projection=ccrs.Robinson(), llc=(-179.9999, -60.), urc=(179.9999, 80),
           extend=(0,1), cmap=plt.get_cmap('jet'), coastline_size='110m', title=None,
           flip_ud = False, veg_mask=SMECV_Grid_v042('rainforest').get_grid_points()[0],
           gridspace=(60,20), grid_loc='0011', ocean=True, land=True, interface=True,
           cbar_location='bottom', cbar_label=None, cbar_kwargs=None):

    '''

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with gpis as the index or a lat/lon Multiindex
        If index is GPIs be default, we assume that the origin is in the bottom
        left (gpi=0 --> map bottom left), you can activate flip_up=True to reverse
        this assumption.
    col : str
        Name of the column in the data frame that will be plotted
    grid : pygeogrids.Grid, optional (default: None)
        Grid that is used to look up the gpi-index of the df.
        If the index is already a lon/lat Multiindex, this can remain None as it
        is not used then.
    projection : cartopy.projection
        Projection of the map, as implemented in cp
    llc : tuple, optional (default: (-179.9999, -60.))
        Coordinates (in the data CRS) of the lower left corner of the subset to plot
    urc : tuple, optional (default: (179.9999, 80))
        Coordinates (in the data CRS) of the upper right corner of the subset to plot
    extend : tuple, optional (default: (0,1))
        Extent of values to plot
    cmap : colormap, optional (default: plt.get_cmap('jet'))
        A colormap object as returned by plt.get_cmap()
    coastline_size : str, optional (default: '110m')
        A string that indicates the size of the coastlines to plot (e.g '110m')
    veg_mask : np.array or None, optional (default: ESA CCI 0.25deg rainforest mask)
        Array of GPIs that are masked by as densly vegetated or array of tuples
        with location (lons, lats) that are masked or None, if nothing should be
        masked.
    gridspace
    grid_loc : str
        top, right, bottom, left
        1111 to print all grids, 0011 to print the bottom and left grid etc.
    ocean
    land
    cbar_kwargs : dict
        See https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html

    Returns
    -------

    '''
    if isinstance(df.index, pd.MultiIndex):
        gpi_index = False
        lats = df.index.get_level_values('lat').values
        lons = df.index.get_level_values('lon').values
        if grid is not None:
            print('Looking up locations in grid')
            df['gpi'], df['dist'] = grid.find_nearest_gpi(lons, lats)

        else:
            print('No grid passed, generating generic gpis')
            grid = BasicGrid(lon=lons, lat=lats).to_cell_grid(5.)
            df['gpi'], df['dist'] = grid.find_nearest_gpi(lons, lats)

    else:
        gpi_index = True
        if grid is None:
            raise ValueError('DF does not contain a MultiIndex, pass a grid, so that we can link the GPIs to locations.')

        print('Looking up locations in grid')
        lons, lats = grid.gpi2lonlat(df.index)
        df['gpi'] = df.index
        df['lon'] = lons
        df['lat'] = lats
        df = df.set_index(['lat', 'lon'])


    #img = np.empty(df.index.size, dtype='float32')
    #img.fill(np.nan)
    #img[df.index] = df[col].values

    #img_masked = np.ma.masked_invalid(img.reshape((180 * 4, 360 * 4)))

    f = plt.figure(num=None, figsize=(8, 4), dpi=200, facecolor='w', edgecolor='k')

    data_crs = ccrs.PlateCarree()

    imax = plt.axes(projection=projection)
    imax.coastlines(resolution=coastline_size)

    if ocean:
        imax.add_feature(cartopy.feature.OCEAN, zorder=0)
    if land:
        imax.add_feature(cartopy.feature.LAND, zorder=0)

    if gridspace is not None:
        minx, maxx = np.round(llc[0]), np.round(urc[0])
        miny, maxy = np.round(llc[1]), np.round(urc[1])
        dx, dy = gridspace[0], gridspace[1]
        gl = imax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False,
                            linewidth=1, color='black', alpha=0.2, linestyle='--')

        xlocs = np.arange(minx, maxx + dx, dx)
        ylocs = np.arange(miny, maxy + dy, dy)
        gl.xlocator = mticker.FixedLocator(xlocs)
        gl.ylocator = mticker.FixedLocator(ylocs)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER

        spher = is_spherical(projection)
        grid_kwargs = {p: True if g=='1' else False for p, g in zip(['top', 'rgt', 'bot', 'lft'], grid_loc)}
        add_grid_labels(imax, minx, maxx, miny, maxy, dx, dy,
                        spherical=spher, edgle_label_x=False,
                        edge_label_y=True if spher else False,
                        **grid_kwargs)


    if llc is not None and urc is not None:
        imax.set_extent([llc[0], urc[0], llc[1], urc[1]], crs=data_crs)

    lats = np.sort(np.unique(df.index.get_level_values('lat')))
    lons = np.unique(df.index.get_level_values('lon'))

    n_lats = lats.size
    n_lons = lons.size

    data = df[col].values
    data = np.ma.masked_invalid(data.reshape((n_lats, n_lons)))
    data = np.flipud(data)

    lons, lats = np.meshgrid(lons, np.flipud(lats))

    if flip_ud:
        data = np.flipud(data)

    im = imax.pcolormesh(lons, lats, data, cmap=cmap, transform=data_crs)

    im.set_clim(vmin=extend[0], vmax=extend[1])

    if veg_mask is not None:
        df['veg_mask'] = np.nan
        if veg_mask.ndim > 1:
            veg_lons = veg_mask[:, 0]
            veg_lats = veg_mask[:, 1]
            veg_gpis, veg_gpi_dist = grid.find_nearest_gpi(veg_lons, veg_lats)

        else:
            veg_gpis = veg_mask
            veg_lons, veg_lats = grid.gpi2lonlat(veg_mask)

        df_veg = pd.DataFrame(data={'veg_lon': veg_lons, 'veg_lat': veg_lats,
                                    'veg_gpis': veg_gpis})

        df.loc[df['gpi'].isin(df_veg['veg_gpis']), 'veg_mask'] = 1.

        data = df['veg_mask'].values
        data = np.ma.masked_invalid(data.reshape((n_lats, n_lons)))
        data = np.flipud(data)

        colors = [(7. / 255., 79. / 255., 25. / 255.), (1., 1., 1.)]  # dark greeb
        vegcmap = LinearSegmentedColormap.from_list('Veg', colors, N=2)

        imax.pcolormesh(lons, lats, data, cmap=vegcmap, transform=data_crs)

    if interface:
        # colorbar
        cbar = plt.colorbar(im, ax=imax, **cbar_kwargs)
        # cb.ax.yaxis.set_ticks_position('left')
        if cbar_label:
            cbar.set_label(cbar_label)

        # title
        if title: f.suptitle(title, fontsize=10)




    return f, imax, im


