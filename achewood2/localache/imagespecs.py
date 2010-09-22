from imagekit.specs import ImageSpec
from imagekit import processors

## RESIZORS
class ResizeThumbelina(processors.Resize):
	width = 64
	height = 64
	crop = True

class ResizeThumb(processors.Resize):
	width = 200
	height = 200
	crop = True

class ResizeAdminThumb(processors.Resize):
	width = 200
	height = 200
	crop = True

class ResizeDisplay(processors.Resize):
	width = 600

class ResizeDisplay(processors.Resize):
	width = 600

## ENHANCE!!!!!
class EnhanceThumb(processors.Adjustment):
	contrast = 1.2
	sharpness = 1.1

class JPEGFormatter(processors.Format):
	format = 'JPEG'
	extension = 'jpg'

class VanillaICC(processors.ICCTransform):
	source = '/Library/Application Support/Adobe/Color/Profiles/Recommended/sRGB Color Space Profile.icm' # sRGB 61966-2.1
	#destination = '/Library/Printers/Canon/BJPrinter/Resources/ICCProfiles/Pro9000.canonicc/Contents/Resources/Canon Pro9000 GL1.icc' # Canon 9000 Bubblejet Fine Art
	destination = '/Library/Application Support/Adobe/Color/Profiles/Recommended/sRGB Color Space Profile.icm' # sRGB 61966-2.1



## actual image specs
class AdminThumbnail(ImageSpec):
	#quality = 80
	access_as = "adminthumb"
	pre_cache = True
	processors = [VanillaICC, JPEGFormatter, ResizeAdminThumb, EnhanceThumb]

class Thumbnail(ImageSpec):
	#quality = 80
	access_as = 'thumb'
	pre_cache = True
	processors = [VanillaICC, JPEGFormatter, ResizeThumb, EnhanceThumb]
	
class Thumbelina(ImageSpec):
	#quality = 80
	access_as = 'thumbelina'
	pre_cache = True
	processors = [VanillaICC, JPEGFormatter, ResizeThumbelina, EnhanceThumb]

class Display(ImageSpec):
	#quality = 80
	access_as = 'display'
	pre_cache = True
	processors = [VanillaICC, JPEGFormatter, ResizeDisplay]


