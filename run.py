from update import init_config, main

main.Downloads().download()

main.ToJosn().srs()

main.MergeJsonConfig().merge()

g = main.Generate()
g.inline()
g.dns()
g.platform()