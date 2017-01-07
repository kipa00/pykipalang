# kipalang
kipa's first well-constructed language starting from 3-day coding.

## installation
Download parsexpr.py and put it to the path of your python program.

## parsexpr.py documentation
There are some functions you can use to interpret kipalang scripts.

<code>parsexpr.evaluate(s)</code> evaluates <code>s</code> as a kipalang script and returns the result.
Note that the script execution can be restricted by print buffer length or time limitation.

<code>parsexpr.setBufferSize(l)</code> restricts print buffer length to <code>l</code>.
If <code>l</code> is omitted or less than zero then this removes the buffer length restriction.

<code>parsexpr.setTimeout(t)</code> resticts the script exection time up to <code>t</code> second(s).
If <code>t</code> is omitted or less than zero then this removes the execution time limitation.
