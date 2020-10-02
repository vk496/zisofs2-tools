from mkzftree2.arguments import get_parser
from mkzftree2.models.FileObject import FileObject, ZISOFSv2
from mkzftree2.file_process import find_files, compress_big


def main(args=None):
    parser = get_parser()
    opt = parser.parse_args(args)

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

    ZISOFSv2.set_blocksize(blocksize)
    ZISOFSv2.set_compressor(opt.a)

    # Recursive search of all files
    find_files(source)

    compress_big(opt.a, opt.z, blocksize, force=opt.force)


    # Process
    # d = FileObject.get_smallfiles()
    print("Hola")

if __name__ == '__main__':
    # execute only if run as the entry point into the program
    main()