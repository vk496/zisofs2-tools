from mkzftree2.arguments import get_options
from mkzftree2.models.FileObject import FileObject, ZISOFS, ZISOFSv2
import mkzftree2.file_process as fp


def main(args=None):
    opt = get_options(args)

    source = opt.intree[0]
    target = opt.outtree[0]
    blocksize = opt.blocksize * 2**10

    # Create targer directory
    try:
        target.mkdir(parents=True)
    except FileExistsError: # We already checked that is a empty dir
        pass
    
    # We will use this
    FileObject.target_dir = target
    FileObject.source_dir = source

    ZISOFS.set_blocksize(blocksize)

    if not opt.legacy:
        ZISOFSv2.set_compressor(opt.a)

    # Recursive search of all files
    fp.find_files(source, opt.legacy)

    fp.compress_file(opt.a, opt.z, blocksize, force=opt.force)


    # Process
    # d = FileObject.get_smallfiles()
    print("Hola")

if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()