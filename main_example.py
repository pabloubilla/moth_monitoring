from bokeh.plotting import figure, output_file, show
from bokeh.models import Div, Spinner, TextInput, ColumnDataSource, CustomJS
import numpy as np
from bokeh.layouts import layout

### this is just an example to show how to use the Spinner widget in Bokeh ###

### https://www.youtube.com/watch?v=HDvxYoRadcA&ab_channel=NeuralNine ###

# Initial value of a
a = 1

# x from 1 to 10
x = np.linspace(1, 10, 100)

# Initial y line
y = x + a

# Create a ColumnDataSource: it's needed for updating plot data
source = ColumnDataSource(data=dict(x=x, y=y))

p = figure(x_axis_label='x', y_axis_label='y')

# Use the source for the line
line = p.line('x', 'y', source=source, line_width=2, color="blue")

div = Div(text="""<b>Change the line color and the value of a</b>""")
color = TextInput(value="blue", title="Line Color:")
color.js_link('value', line.glyph, 'line_color')

# Spinner for changing the value of a
spinner = Spinner(title="Value of a:", low=-10, high=10, step=0.1, value=1)

# JavaScript to update y based on a
callback = CustomJS(args=dict(source=source, spinner=spinner), code="""
    const data = source.data;
    const A = spinner.value;
    const x = data['x'];
    const y = data['y'];
    for (let i = 0; i < x.length; i++) {
        y[i] = Math.log(x[i]) + A;
    }
    source.change.emit();
""")

# Link spinner to the callback
spinner.js_on_change('value', callback)

# Arrange layout
layout = layout([[div, color, spinner], [p]])
show(layout)
