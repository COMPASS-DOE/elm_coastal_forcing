library(ncdf4)
library(terra)
library(sf)
library(rgdal)
library(rgeos)
library(dplyr)

setwd('/Users/flue473/Downloads/SWOT_L2_HR_PIXC_489_010_051R_20230413T032943_20230413T032954_PIB0_01')

names(nc$var)
# dim(nc$var)

print(nc)

r <- rast(nc, 'classification_qual')


nc <- nc_open('SWOT_L2_HR_PIXC_489_010_051R_20230413T032943_20230413T032954_PIB0_01.nc')

# NOTE how not specifying varid reads the "only" var in the file
# data <- ncvar_get( nc )	


# pixel cloud/height vs. lat/lon
variables <- c('latitude','longitude','height')

lat <- ncvar_get(nc , 'pixel_cloud/latitude')
lon <- ncvar_get(nc , 'pixel_cloud/longitude')
height <- ncvar_get(nc , 'pixel_cloud/height')

# nc_close(nc)

dt <- cbind(lat, lon, height)
df <- data.frame(dt)

pts <- SpatialPointsDataFrame(coords<-cbind(lat,lon),data=data.frame(height))

pts_sf <- st_as_sf(pts)

Grid <- SpatialPixelsDataFrame(points=pts, grid=NULL, data=height, tolerance=0.1)

# /----------------------------------------------------------------------------
#/
library(ggplot2)

ggplot()+
  geom_point(data=df, aes(x=lon, y=lat, color=height))



ggplot()+
  geom_sf(data=pts[1:100,], aes(x=lon, y=lat, color=height))
