
getwd()
library(here)
here()

library(tidyverse)
library(ggplot2)
library(here)

setwd('/Users/flue473/Documents/projects/compass_fme/erie_tempest')


# /----------------------------------------------------------------------------#
#/  Prep data


#######
library(forcats)


df <- read.csv('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/elm_pflotran/data/site_pts/all/dswe/all_sites_dswe_inundperc.csv') %>% 
  filter(!zone %in% c('water','sediment')) %>% 
  filter(site_cat=='synoptic') %>% 
  filter(region=='Chesapeake Bay') %>% 
  select('site_id','site_cat','wetperc','zone') %>% 
  mutate(zone = fct_relevel(zone,  'Wetland','Transition','Upland'))

glimpse(df)


ggplot() +
  geom_tile(data=df,
            aes(x=zone, y=site_id, fill=wetperc), color='white', lwd=2) +
  
  geom_text(data=df, aes(x=zone, y=site_id, label=round(wetperc,2))) +
  
  scale_fill_distiller(palette='YlGnBu', direction=1) +
  ggtitle("DSWE water/wetland % of observation (Landsat 7&8) over 2000-2024") +
  ylab('') +
  xlab('') +
  theme_minimal()







# 
# 
# #######################
# df <- read.csv('/Users/flue473/Library/CloudStorage/OneDrive-PNNL/Documents/projects/compass_fme/elm_pflotran/data/site_pts/all/dswe/all_sites_dswehist.csv') %>% 
#   select(-.geo) %>% 
#   filter(zone != 'water') %>% 
#   filter(site_cat=='synoptic') %>% 
#   filter(region=='Chesapeake Bay') %>% 
#   # arrange(name) %>% 
#   # filter(name == "Upper South Creek") %>%
#   mutate(system.index = str_remove(system.index, "1_1_LE07_015034_")) %>% 
#   mutate(system.index = str_remove(system.index, "1_1_LE07_014033_")) %>% 
#   mutate(system.index = str_remove(system.index, "1_2_LE07_014034_")) %>% 
#   mutate(system.index = str_remove(system.index, "1_2_LE07_014033_")) %>% 
#   mutate(system.index = str_remove(system.index, "1_1_LE07_014034_")) %>% 
#   
#   mutate(date = str_split(system.index, "_", simplify = TRUE)[,1]) %>% 
#   mutate(date = as.Date(date, "%Y%m%d")) %>% 
#   
#   arrange(date) %>% 
#   # filter(mean>0.0) %>%
#   # Group by month + year
#   mutate(month_yr = format(date, "%Y-%m")) %>% 
#   group_by(month_yr) %>% 
#   summarize(mean = mean(mean, na.rm=T)) %>% 
#   ungroup() #%>% 
#   # mutate(date=as.Date(paste0(month_yr,'-01'), format= "%Y-%m-%d")) %>% 
#   # filter(date > as.Date("2010-01-01"))
# 
# 
# glimpse(df)
# 
# 
# 
# 
# 
# 
# 
# 
# 
# # /----------------------------------------------------------------------------#
# #/ Make plot
# 
# dswe_ts <- 
#   ggplot(df) +
#   geom_line(aes(x=date, y=mean), color='blue3') +
#   geom_point(aes(x=date, y=mean), color='blue3', size=0.4) +
#   xlab("Date") +
#   ylab("Fraction of Upper South Creek inundated\n(Landsat DSWE; Jones et al. 2019)") +
#   scale_x_date(expand=c(0,0)) +
#   scale_y_continuous(limits=c(0,1), breaks=c(0, 0.25, 0.5, 0.75, 1), expand=c(0,0)) +
#   theme_bw() +
#   theme(panel.grid.minor = element_blank()) 
# 
# 
# dswe_ts
# 
# 
# # /----------------------------------------------------------------------------#
# #/ save plot
# 
# ggsave("./output/figures/dswe_uppersouthcreek_post2010.png", dswe_ts,
#        dpi=400, width=180, height=100, units='mm') #, type = "cairo-png")
# 
# dev.off()
