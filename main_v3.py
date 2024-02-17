from bokeh.plotting import figure, output_file, show
from bokeh.models import Div, Spinner, TextInput
import numpy as np
from bokeh.layouts import layout

# x from 1 to 10
x = np.linspace(1, 10, 100)
a = 1


# different y lines
y1 = np.log(x) + a

p = figure(title="log(x) and log(x)+1 and log(x)+2", x_axis_label='x', y_axis_label='y')
line = p.line(x, y1, line_width=2, color="blue")

div = Div(text="""<b>Change the line color</b>""")
color = TextInput(value="blue", title="Line Color:")
color.js_link('value', line.glyph, 'line_color')

layout = layout([[div, color], [p]])
show(layout)
