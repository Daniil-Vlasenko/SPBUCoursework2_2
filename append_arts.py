import math

from PIL import Image

class Append():
    def append_images_square(self, images, direction='horizontal', aligment='center', bg_color=(255, 255, 255)):
        """
        Метод объединает картины в квадрат

        :param images: Скписок картин PIL images
        :param direction: Расположение картин ('horizontal' или 'vertical')
        :param aligment: Расположить относительно какой стороны результирующей картины ('left', 'right', 'top', 'bottom', или 'center')
        :param bg_color: Цвет фона

        :return: Результирующая картинка PIL image object
        """
        widths = [images[0].size[0], images[1].size[0]]
        heights = [images[0].size[1], images[1].size[1]]

        # приводим размеры картин так, чтобы картины были примерно одного размера
        if widths[0] > widths[1]:
            koef = widths[1] / widths[0]
            widths[0] = widths[1]
            heights[0] = int(heights[0] * koef)

            if heights[0] > heights[1]:
                koef = heights[1] / heights[0]
                heights[0] = heights[1]
                widths[0] = int(widths[0] * koef)

            else:
                koef = heights[0] / heights[1]
                heights[1] = heights[0]
                widths[1] = int(widths[1] * koef)

        else:
            koef = widths[0] / widths[1]
            widths[1] = widths[0]
            heights[1] = int(heights[1] * koef)

            if heights[0] > heights[1]:
                koef = heights[1] / heights[0]
                heights[0] = heights[1]
                widths[0] = int(widths[0] * koef)

            else:
                koef = heights[0] / heights[1]
                heights[1] = heights[0]
                widths[1] = int(widths[1] * koef)

        images[0] = images[0].resize((widths[0], heights[0]), Image.ANTIALIAS)
        images[1] = images[1].resize((widths[1], heights[1]), Image.ANTIALIAS)

        if direction == 'horizontal':
            frame = int(0.03 * sum(widths))
            space = int(0.06 * sum(widths))
            new_width = sum(widths) + space + frame * 2
            new_height = max(heights)
        else:
            frame = int(0.03 * sum(heights))
            space = int(0.06 * sum(heights))
            new_width = max(widths)
            new_height = sum(heights) + space + frame * 2

        length = max(new_width, new_height)
        new_im = Image.new('RGB', (length, length), color=bg_color)

        offset = frame
        for im in images:
            if direction == 'horizontal':
                y = 0
                if aligment == 'center':
                    y = int((length - im.size[1]) / 2)
                elif aligment == 'bottom':
                    y = length - im.size[1]
                new_im.paste(im, (offset, y))
                offset += im.size[0] + space
            else:
                x = 0
                if aligment == 'center':
                    x = int((length - im.size[0]) / 2)
                elif aligment == 'right':
                    x = length - im.size[0]
                new_im.paste(im, (x, offset))
                offset += im.size[1] + space

        return new_im

    def append_images_square_minimum_background(self, images, aligment = "center", bg_color=(255, 255, 255)):
        """
        Метод объединает картины в квадрат

        :param images: Скписок картин PIL images
        :param aligment: Расположить относительно какой стороны результирующей картины ('left', 'right', 'top', 'bottom', или 'center')
        :param bg_color: Цвет фона

        :return: Результирующая картинка PIL image object
        """
        widths = [images[0].size[0], images[1].size[0]]
        heights = [images[0].size[1], images[1].size[1]]

        # приводим размеры картин так, чтобы картины были примерно одного размера
        if widths[0] > widths[1]:
            koef = widths[1] / widths[0]
            widths[0] = widths[1]
            heights[0] = int(heights[0] * koef)

            if heights[0] > heights[1]:
                koef = heights[1] / heights[0]
                heights[0] = heights[1]
                widths[0] = int(widths[0] * koef)

            else:
                koef = heights[0] / heights[1]
                heights[1] = heights[0]
                widths[1] = int(widths[1] * koef)

        else:
            koef = widths[0] / widths[1]
            widths[1] = widths[0]
            heights[1] = int(heights[1] * koef)

            if heights[0] > heights[1]:
                koef = heights[1] / heights[0]
                heights[0] = heights[1]
                widths[0] = int(widths[0] * koef)

            else:
                koef = heights[0] / heights[1]
                heights[1] = heights[0]
                widths[1] = int(widths[1] * koef)

        images[0] = images[0].resize((widths[0], heights[0]), Image.ANTIALIAS)
        images[1] = images[1].resize((widths[1], heights[1]), Image.ANTIALIAS)

        if heights[0] >= widths[0] and heights[1] >= widths[1]:
            frame = int(0.02 * sum(widths))
            space = int(0.04 * sum(widths))
            new_width = widths[0] + widths[1] + space + frame * 2
            new_height = max(heights[0], heights[1])
            length = max(new_width, new_height)
            direction = 'horizontal'
        elif heights[0] <= widths[0] and heights[1] <= widths[1]:
            frame = int(0.02 * sum(heights))
            space = int(0.04 * sum(heights))
            new_width = max(widths[0], widths[1])
            new_height = heights[0] + heights[1] + space + frame * 2
            length = max(new_width, new_height)
            direction = 'vertical'
        else:
            if heights[0] + heights[1] >= widths[0] + widths[1]:
                frame = int(0.02 * sum(widths))
                space = int(0.04 * sum(widths))
                new_width = widths[0] + widths[1] + space + frame * 2
                new_height = max(heights[0], heights[1])
                length = max(new_width, new_height)
                direction = 'horizontal'
            else:
                frame = int(0.02 * sum(heights))
                space = int(0.04 * sum(heights))
                new_width = max(widths[0], widths[1])
                new_height = heights[0] + heights[1] + space + frame * 2
                length = max(new_width, new_height)
                direction = 'vertical'

        new_im = Image.new('RGB', (length, length), color=bg_color)

        offset = frame
        for im in images:
            if direction == 'horizontal':
                y = 0
                if aligment == 'center':
                    y = int((length - im.size[1]) / 2)
                elif aligment == 'bottom':
                    y = length - im.size[1]
                new_im.paste(im, (offset, y))
                offset += im.size[0] + space
            else:
                x = 0
                if aligment == 'center':
                    x = int((length - im.size[0]) / 2)
                elif aligment == 'right':
                    x = length - im.size[0]
                new_im.paste(im, (x, offset))
                offset += im.size[1] + space

        return [new_im, direction]

    def stories(self, images,  bg_color=(255, 255, 255)):
        """
        Создает два изображения, которые по размеру подойдут для публикации в stories
        в формате коллажа в Instagramm. Коллаж для двух картин, где размер каждой 33 к 40

        :param images: Скписок картин PIL images
        :param bg_color:
        :return: Цвет фона
        """
        widths = [images[0].size[0], images[1].size[0]]
        heights = [images[0].size[1], images[1].size[1]]
        newImage = []

        for i in range(2):
            if math.fabs(widths[i] - heights[i]) <= widths[i] * 0.05 or math.fabs(widths[i] - heights[i]) <= heights[i] * 0.05:
                frame = int(0.05 * widths[i])
                newHeight = int(frame * 2 + heights[i])
                newWidth = int(newHeight * 40 / 33)
                direction = 'center'
            elif widths[i] > heights[i]:
                frame = int(0.05 * widths[i])
                newWidth = int(frame * 2 + widths[i])
                newHeight = int(newWidth * 33 / 40)
                direction = 'horizontal'
            else:
                frame = int(0.05 * heights[i])
                newHeight = int(frame * 2 + heights[i])
                newWidth = int(newHeight * 40 / 33)
                direction = 'vertical'

            new_im = Image.new('RGB', (newWidth, newHeight), color=bg_color)

            if direction == 'horizontal' :
                y = int((newHeight - heights[i]) / 2)
                new_im.paste(images[i], (frame, y))
            else:
                x = int((newWidth - widths[i]) / 2)
                new_im.paste(images[i], (x, frame))

            newImage.append(new_im)

        return newImage







