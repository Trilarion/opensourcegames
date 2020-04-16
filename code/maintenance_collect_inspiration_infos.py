from utils import constants as c, utils, osg

if __name__ == "__main__":

    inspirations = osg.read_inspirations_info()
    osg.write_inspirations_info(inspirations)  # write again just to check integrity

    # assemble info
    entries = osg.assemble_infos()