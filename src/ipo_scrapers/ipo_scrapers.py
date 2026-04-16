from src.ipo_scrapers.chittorgarh_scraper import ChittorgarhScraper

def get_scraper(config):
    source = config["scraper"]["source"]

    if(source == "CHITTORGARH" or source == "DEFAULT"):
        return ChittorgarhScraper()
    else:
        raise RuntimeError(f"Unsupported scraper source: {source}")