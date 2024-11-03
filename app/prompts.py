first_prompt = """
You are a cognitive scientist and UX expert tasked with conceptualizing a visually appealing and functional website to replace spreadsheet-based data analysis for {what_and_why}. Your goal is to create a design that makes qualitative data visualization custom and useful, and easy to reason on.

Here is the data example:
{json_data}

You are an AI assistant specializing in UX design and data visualization. Your task is to help create a detailed design brief for a a junior developer to build for a user who needs their data visualized so they can go through it easier. This brief will guide a junior developer in building a user-friendly, visually appealing, and functional website to replace spreadsheet-based data analysis.
Before generating the brief, you will be provided with:

A description of the project's purpose and context
Information about the type of data being analyzed
Details about the intended users
Any specific goals or challenges to address

After receiving this context, analyze the information and use the following XML structure to generate a comprehensive design brief:


<brief_generation_instructions>
  <data_analysis>
    Analyze the described data to determine:
    <key_points>
      <point>Primary data types (e.g., text, numbers, dates, categorical)</point>
      <point>Data structure (e.g., hierarchical, tabular, relational)</point>
      <point>Potential patterns or relationships</point>
      <point>Estimated data volume and complexity</point>
    </key_points>
  </data_analysis>

  <use_case_elaboration>
    Based on the provided context, elaborate on:
    <elements>
      <element>Specific user needs and pain points</element>
      <element>Key tasks users will perform with the data</element>
      <element>How the tool will improve upon current spreadsheet-based analysis</element>
    </elements>
  </use_case_elaboration>

  <design_requirements>
    Generate tailored design requirements:
    <elements>
      <element>
        <name>Layout Structure</name>
        <description>Optimal layout for data presentation</description>
      </element>
      <element>
        <name>Data Visualization</name>
        <description>Appropriate charts, graphs, or visualizations. Here are the options: Chart Area, Chart Bar, Chart Line, Chart Pie

Only use visualziers if necessary, use other components if need be, do not force using charts.
</description>
      </element>
      <element>
        <name>Interactivity</name>
        <description>Necessary interactive features (this is limited to front end functionality only, nothing that requires saving stuff to the backend) This coukd be search, filters, clickable links etc.</description>
      </element>
  </design_requirements>

<color-guide>
Guide: Vercel style website, light mode while using other colors appropriately. Make sure each bar/ item of the chart is colored differently.
</color-guide>

Under no circumstances are you allowed to just throw a chart on the website and call it a day. Think of how those Covid tracker websites helped people interact with covid data. You will allow for that but for any data and that does not just happen with charts, it can happen with all different types of website components and pieces using Shadcn. Only use charts and visualizations when ABSOLUTELY neccesary.

Remember these are interactive websites and charts may or may not be needed. Think about how we can just make the user have a better experience with looking through and interacting with their data easily. Think of this as a new way to go through datasets with a perfectly tailored website. Use your tools wisely. 

Be creative yet professional. Make the website well rounded and optimized for human cognitive ease and relief of not having to be overwhelmed by boring to consume data.

You need to make sure that the content design fills up the entire window and that you use the colors mentioned.


  <user_interface_guidelines>
    Provide specific UI guidelines for:
    <aspects>
(insert custom design here)
    </aspects>
  </user_interface_guidelines>

  <functionality_specifications>
    Detail key functionalities:
    <features>
        <name>Data How will it make it easier to interact with this data specifically?</name>
        <description>Explain what the nature of the data is and how it can be consumed in the easiest way possible</description>
    </features>
  </functionality_specifications>

  <data_handling_strategies>
    Outline strategies for:
    <strategies>
      <strategy>Handling missing or incomplete data</strategy>
      <strategy>Managing data updates or real-time data flows</strategy>
      <strategy>Ensuring data integrity and validation</strategy>
      <strategy>Optimizing performance for the data volume and complexity</strategy>
    </strategies>
  </data_handling_strategies>

  <accessibility_and_usability>
    Provide guidelines for:
    <guidelines>
      <guideline>Color contrast and readability</guideline>
      <guideline>Keyboard navigation and screen reader compatibility</guideline>
      <guideline>Clear and consistent labeling and instructions</guideline>
      <guideline>Error handling and user feedback mechanisms</guideline>
    </guidelines>
  </accessibility_and_usability>

  <example_components>
    Generate 3 good and 3 bad examples of components or design elements:
    <good_examples>
      <example>A well-designed component that effectively presents a key aspect of the data</example>
      <example>An intuitive interaction method suited to the data structure</example>
      <example>An efficient data entry interface if applicable to the use case</example>
    </good_examples>
    <bad_examples>
      <example>A poorly chosen visualization that misrepresents the data</example>
      <example>An overly complex interface element that hinders data understanding</example>
      <example>A design choice that doesn't scale well with the observed data volume</example>
    </bad_examples>
  </example_components>

  <next_steps>
    Outline:
    <steps>
      <step>Prototyping priorities</step>
      <step>Potential challenges specific to this data and use case</step>
      <step>Areas for further data analysis or user research</step>
    </steps>
  </next_steps>
</brief_generation_instructions>

You are essentially building a custom looker studio/ interactive dashboard generative website for the user on the fly.

Do not suggest charts if charts do not help.

The point of this is you are supposed to come up with all of these answers custom to what kind of website would help the user interact and reason on their data better.

Remember the developer you are giving this to is just a junior engineer so he will try his best but do not have crazy expectations or confuse him. Remeber the user must not be able to input anything into the UI or to be able to update the data, there is no backend to save what they enter.
    """
    
    
    
    
    
second_prompt = """
  You are making a frontend/ non-functioning but fully fleshed out UI prototype that looks as if vercel made it.

    Create a non functioning UI using only ShadCN components to visualize this dataset {what_and_why} while considering these instructions: {first_response}. Use this sample data directly in the script:

    {json_data}

    Follow these guidelines:
    1. Use only ShadCN components compatible with NextJS.
    2. Import each ShadCN component individually from "@/components/ui/[component-name]".
    3. Do not use Date Picker, Data Table components or theme provider.
    4. Focus on displaying information without any interactive features or API calls, unless that interactive feature is simply handled by a link click and you have or can make the link.
    5. Write the entire TSX file from start to finish, including all necessary imports and type definitions.
    6. Ensure the code is complete and ready for the developer to finish based on your prototype use without any placeholders or TODO comments.
    7. The script should directly use the sample data provided above.
    8. If you are told to make a button but do not have a link to send them or do not know, do not make it.
    9. If something looks like it is clickable or a button, it must be clickable and take them somewhere, if not do not make it look like a button. If it is a link displayed, it must be clickable.
    10. Make sure the formatting is proper and fills up an entire page regardless of what screen they are on.
    11. All buttons and functionality must be the best possoble things to show and let them do.
    12. Data should be visualize how you have been instructed to visualize it and you need to consider the use case and make a fully designed website that will be super helpful and custom when the logic and data is added.
    13. Create a single-page layout where users scroll vertically to access different sections of content, rather than using a tabbed interface with clickable navigation elements.
    

    Here is a guide on how to design and create Shadcn charts using rechart:
    <chart>
    Shadcn's New Rechart Wrapper Guide

1. Introduction

Shadcn's new chart component library provides a powerful and flexible wrapper around recharts, allowing for easy creation and customization of various chart types. This guide will walk you through the process of using the library to create area charts, bar charts, line charts, and pie charts, along with their various options and customizations.

2. Setup and Dependencies

Before we begin, ensure you have the following dependencies installed:

- shadcn/ui
- recharts

You'll also need to have your project set up with the necessary shadcn components and styling.

3. Common Components and Concepts

Before diving into specific chart types, let's familiarize ourselves with some common components and concepts used across all chart types:

a. ChartContainer:
The ChartContainer component is used to wrap all chart types. It provides a consistent layout and styling for your charts.

b. ChartTooltip:
The ChartTooltip component is used to display tooltips when hovering over chart elements.

c. ChartLegend:
The ChartLegend component is used to display a legend for your chart.

d. ChartConfig:
The ChartConfig type is used to define the configuration for your chart, including colors and labels for each data series.

4. Area Charts

Area charts are useful for showing trends over time and comparing multiple data series.

4.1 Basic Area Chart

To create a basic area chart:

1. Import the necessary components:
   import {{ Area, AreaChart, CartesianGrid, XAxis }} from "recharts"
   import {{ ChartContainer, ChartTooltip, ChartTooltipContent }} from "@/components/ui/chart"


   You must import rechart and shadcn the same way you always do, seperetly, do not mix the two in your import statements.

2. Define your chart data:
   const chartData = [
     {{ month: "January", desktop: 186 }},
     {{ month: "February", desktop: 305 }},
     // ... more data points
   ]

3. Define your chart configuration:
   const chartConfig = {{
     desktop: {{
       label: "Desktop",
       color: "hsl(var(--chart-1))",
     }},
   }}

4. Create the chart component:
   <ChartContainer config={{chartConfig}}>
     <AreaChart
       accessibilityLayer
       data={{chartData}}
       margin={{
         left: 12,
         right: 12,
       }}
     >
       <CartesianGrid vertical={{false}} />
       <XAxis
         dataKey="month"
         tickLine={{false}}
         axisLine={{false}}
         tickMargin={{8}}
         tickFormatter={{(value) => value.slice(0, 3)}}
       />
       <ChartTooltip
         cursor={{false}}
         content={{<ChartTooltipContent indicator="line" />}}
       />
       <Area
         dataKey="desktop"
         type="natural"
         fill="var(--color-desktop)"
         fillOpacity={{0.4}}
         stroke="var(--color-desktop)"
       />
     </AreaChart>
   </ChartContainer>

4.2 Area Chart Options

a. Linear vs Natural:
Change the 'type' prop of the Area component to "linear" for straight lines between data points:
<Area
  dataKey="desktop"
  type="linear"
  // ...
/>

b. Step:
Use the "step" type for a step-like appearance:
<Area
  dataKey="desktop"
  type="step"
  // ...
/>

c. Multiple Areas:
Add multiple Area components for comparing different data series:
<Area
  dataKey="desktop"
  // ...
/>
<Area
  dataKey="mobile"
  // ...
/>

d. Stacked Areas:
Add the 'stackId' prop to Area components to create a stacked area chart:
<Area
  dataKey="desktop"
  stackId="a"
  // ...
/>
<Area
  dataKey="mobile"
  stackId="a"
  // ...
/>

e. Expanded Stacked Areas:
Add 'stackOffset="expand"' to the AreaChart component for percentage-based stacking:
<AreaChart
  stackOffset="expand"
  // ...
>
  // ...
</AreaChart>

f. Gradient Fill:
Use a linearGradient for a more visually appealing fill:
<defs>
  <linearGradient id="fillDesktop" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%" stopColor="var(--color-desktop)" stopOpacity={{0.8}} />
    <stop offset="95%" stopColor="var(--color-desktop)" stopOpacity={{0.1}} />
  </linearGradient>
</defs>
<Area
  fill="url(#fillDesktop)"
  // ...
/>

g. Legend:
Add a ChartLegend component for multiple data series:
<ChartLegend content={{<ChartLegendContent />}} />

h. Custom Tooltip:
Customize the ChartTooltipContent component for more control over tooltip appearance and content.

5. Bar Charts

Bar charts are excellent for comparing discrete categories or showing data distribution.

5.1 Basic Bar Chart

To create a basic bar chart:

1. Import the necessary components:
   import {{ Bar, BarChart, CartesianGrid, XAxis }} from "recharts"
   import {{ ChartContainer, ChartTooltip, ChartTooltipContent }} from "@/components/ui/chart"

2. Define your chart data and configuration (similar to area charts).

3. Create the chart component:
   <ChartContainer config={{chartConfig}}>
     <BarChart accessibilityLayer data={{chartData}}>
       <CartesianGrid vertical={{false}} />
       <XAxis
         dataKey="month"
         tickLine={{false}}
         tickMargin={{10}}
         axisLine={{false}}
         tickFormatter={{(value) => value.slice(0, 3)}}
       />
       <ChartTooltip
         cursor={{false}}
         content={{<ChartTooltipContent hideLabel />}}
       />
       <Bar dataKey="desktop" fill="var(--color-desktop)" radius={{8}} />
     </BarChart>
   </ChartContainer>

5.2 Bar Chart Options

a. Horizontal Bars:
Change the layout prop of the BarChart component to "vertical":
<BarChart
  layout="vertical"
  // ...
>
  // ...
</BarChart>

b. Multiple Bars:
Add multiple Bar components for comparing different data series:
<Bar dataKey="desktop" fill="var(--color-desktop)" radius={{4}} />
<Bar dataKey="mobile" fill="var(--color-mobile)" radius={{4}} />

c. Stacked Bars:
Add the 'stackId' prop to Bar components to create a stacked bar chart:
<Bar dataKey="desktop" stackId="a" fill="var(--color-desktop)" radius={{[4, 4, 0, 0]}} />
<Bar dataKey="mobile" stackId="a" fill="var(--color-mobile)" radius={{[0, 0, 4, 4]}} />

d. Labels:
Add labels to your bars using the LabelList component:
<Bar dataKey="desktop" fill="var(--color-desktop)" radius={{8}}>
  <LabelList
    position="top"
    offset={{12}}
    className="fill-foreground"
    fontSize={{12}}
  />
</Bar>

e. Custom Colors:
Use different colors for each bar by providing a custom shape:
<Bar
  dataKey="visitors"
  shape={{{{ fill, x, y, width, height }} => (
    <rect x={{x}} y={{y}} width={{width}} height={{height}} fill={{fill}} rx={{8}} ry={{8}} />
  )}}
/>

f. Active Bar:
Highlight a specific bar using the activeIndex prop:
<Bar
  dataKey="visitors"
  activeIndex={{2}}
  activeBar={{{{ ...props }} => (
    <Rectangle
      {{...props}}
      fillOpacity={{0.8}}
      stroke={{props.payload.fill}}
      strokeDasharray={{4}}
      strokeDashoffset={{4}}
    />
  )}}
/>

g. Negative Values:
Handle negative values by using different colors for positive and negative bars:
<Bar dataKey="visitors">
  {{chartData.map((item) => (
    <Cell
      key={{item.month}}
      fill={{item.visitors > 0 ? "hsl(var(--chart-1))" : "hsl(var(--chart-2))"}}
    />
  ))}}
</Bar>

6. Line Charts

Line charts are ideal for showing trends over time and comparing multiple data series.

6.1 Basic Line Chart

To create a basic line chart:

1. Import the necessary components:
   import {{ CartesianGrid, Line, LineChart, XAxis }} from "recharts"
   import {{ ChartContainer, ChartTooltip, ChartTooltipContent }} from "@/components/ui/chart"

2. Define your chart data and configuration (similar to area charts).

3. Create the chart component:
   <ChartContainer config={{chartConfig}}>
     <LineChart
       accessibilityLayer
       data={{chartData}}
       margin={{
         left: 12,
         right: 12,
       }}
     >
       <CartesianGrid vertical={{false}} />
       <XAxis
         dataKey="month"
         tickLine={{false}}
         axisLine={{false}}
         tickMargin={{8}}
         tickFormatter={{(value) => value.slice(0, 3)}}
       />
       <ChartTooltip
         cursor={{false}}
         content={{<ChartTooltipContent hideLabel />}}
       />
       <Line
         dataKey="desktop"
         type="natural"
         stroke="var(--color-desktop)"
         strokeWidth={{2}}
         dot={{false}}
       />
     </LineChart>
   </ChartContainer>

6.2 Line Chart Options

a. Linear vs Natural:
Change the 'type' prop of the Line component to "linear" for straight lines between data points:
<Line
  dataKey="desktop"
  type="linear"
  // ...
/>

b. Step:
Use the "step" type for a step-like appearance:
<Line
  dataKey="desktop"
  type="step"
  // ...
/>

c. Multiple Lines:
Add multiple Line components for comparing different data series:
<Line
  dataKey="desktop"
  type="monotone"
  stroke="var(--color-desktop)"
  strokeWidth={{2}}
  dot={{false}}
/>
<Line
  dataKey="mobile"
  type="monotone"
  stroke="var(--color-mobile)"
  strokeWidth={{2}}
  dot={{false}}
/>

d. Dots:
Customize the appearance of data points:
<Line
  dataKey="desktop"
  type="natural"
  stroke="var(--color-desktop)"
  strokeWidth={{2}}
  dot={{
    fill: "var(--color-desktop)",
  }}
  activeDot={{
    r: 6,
  }}
/>

e. Custom Dots:
Use custom shapes for data points:
<Line
  dataKey="desktop"
  type="natural"
  stroke="var(--color-desktop)"
  strokeWidth={{2}}
  dot={{{{ cx, cy, payload }} => (
    <CustomShape
      x={{cx}}
      y={{cy}}
      payload={{payload}}
    />
  )}}
/>

f. Labels:
Add labels to your lines using the LabelList component:
<Line
  dataKey="desktop"
  type="natural"
  stroke="var(--color-desktop)"
  strokeWidth={{2}}
>
  <LabelList
    position="top"
    offset={{12}}
    className="fill-foreground"
    fontSize={{12}}
  />
</Line>

g. Custom Labels:
Customize label content and appearance:
<LabelList
  position="top"
  offset={{12}}
  className="fill-foreground"
  fontSize={{12}}
  dataKey="browser"
  formatter={{(value) => chartConfig[value]?.label}}
/>

7. Pie Charts

Pie charts are useful for showing the composition of a whole and comparing parts of a whole.

7.1 Basic Pie Chart

To create a basic pie chart:

1. Import the necessary components:
   import {{ Pie, PieChart }} from "recharts"
   import {{ ChartContainer, ChartTooltip, ChartTooltipContent }} from "@/components/ui/chart"

2. Define your chart data:
   const chartData = [
     {{ browser: "chrome", visitors: 275, fill: "var(--color-chrome)" }},
     {{ browser: "safari", visitors: 200, fill: "var(--color-safari)" }},
     // ... more data points
   ]

3. Define your chart configuration:
   const chartConfig = {{
     visitors: {{
       label: "Visitors",
     }},
     chrome: {{
       label: "Chrome",
       color: "hsl(var(--chart-1))",
     }},
     // ... more configurations
   }}

4. Create the chart component:
   <ChartContainer config={{chartConfig}}>
     <PieChart>
       <ChartTooltip
         cursor={{false}}
         content={{<ChartTooltipContent hideLabel />}}
       />
       <Pie data={{chartData}} dataKey="visitors" nameKey="browser" />
     </PieChart>
   </ChartContainer>

7.2 Pie Chart Options

a. Donut Chart:
Add an innerRadius prop to create a donut chart:
<Pie
  data={{chartData}}
  dataKey="visitors"
  nameKey="browser"
  innerRadius={{60}}
/>

b. Labels:
Add labels to your pie slices:
<Pie
  data={{chartData}}
  dataKey="visitors"
  label
  nameKey="browser"
/>

c. Custom Labels:
Customize label content and appearance:
<Pie
  data={{chartData}}
  dataKey="visitors"
  labelLine={{false}}
  label={{{{ payload, ...props }} => (
    <text
      {{...props}}
      fill="hsla(var(--foreground))"
    >
      {{`${{chartConfig[payload.browser]?.label}} (${{payload.visitors}})`}}
    </text>
  )}}
  nameKey="browser"
/>

d. Legend:
Add a ChartLegend component:
<ChartLegend
  content={{<ChartLegendContent nameKey="browser" />}}
  className="-translate-y-2 flex-wrap gap-2 [&>*]:basis-1/4 [&>*]:justify-center"
/>

e. Active Slice:
Highlight a specific slice using the activeIndex prop:
<Pie
  data={{chartData}}
  dataKey="visitors"
  nameKey="browser"
  activeIndex={{0}}
  activeShape={{{{ outerRadius = 0, ...props }} => (
    <Sector {{...props}} outerRadius={{outerRadius + 10}} />
  )}}
/>

f. Nested Pie Charts:
Create nested pie charts by using multiple Pie components with different radii:
<Pie data={{desktopData}} dataKey="desktop" outerRadius={{60}} />
<Pie
  data={{mobileData}}
  dataKey="mobile"
  innerRadius={{70}}
  outerRadius={{90}}
/>

g. Center Text:
Add text in the center of a donut chart:
<Pie
  data={{chartData}}
  dataKey="visitors"
  nameKey="browser"
  innerRadius={{60}}
>
  <Label
    content={{{{ viewBox }} => (
      <text
        x={{viewBox.cx}}
        y={{viewBox.cy}}
        textAnchor="middle"
        dominantBaseline="middle"
      >
        <tspan
          className="fill-foreground text-3xl font-bold"
        >
          {{totalVisitors}}
        </tspan>
        <tspan
          className="fill-muted-foreground"
        >
          Visitors
        </tspan>
      </text>
    )}}
  />
</Pie>

8. Theming and Colors

Shadcn's chart wrapper uses CSS variables for colors, making it easy to customize and theme your charts.

8.1 Default Theme

The default theme provides a set of colors for charts:

:root {{
  --chart-1: 173 58% 39%;
  --chart-2: 12 76% 61%;
  --chart-3: 197 37% 24%;
  --chart-4: 43 74% 66%;
  --chart-5: 27 87% 67%;
}}

For dark mode:

.dark {{
  --chart-1: 220 70% 50%;
  --chart-2: 340 75% 55%;
  --chart-3: 30 80% 55%;
  --chart-4: 280 65% 60%;
  --chart-5: 160 60% 45%;
}}

8.2 Custom Colors

To use custom colors:

1. Define your colors in your CSS:
   :root {{
     --color-chrome: #4285F4;
     --color-safari: #34A853;
     --color-firefox: #EA4335;
     --color-edge: #FBBC05;
     --color-other: #7F7F7F;
   }}

2. Use these colors in your chart configuration:
   const chartConfig = {{
     chrome: {{
       label: "Chrome",
       color: "var(--color-chrome)",
     }},
     safari: {{
       label: "Safari",
       color: "var(--color-safari)",
     }},
     // ... more configurations
   }}

3. Apply colors to chart elements:
   <Pie
     data={{chartData}}
     dataKey="visitors"
     nameKey="browser"
     fill={{(entry) => `var(--color-${{entry.browser}})`}}
   />

8.3 Dynamic Theming

For dynamic theming:

1. Create a theme context and provider.
2. Use the context to dynamically update CSS variables.
3. Wrap your chart components with the theme provider.

9. Responsive Design

9.1 Container Responsiveness

Use responsive classes or CSS to adjust the size of the ChartContainer:

<ChartContainer
  config={{chartConfig}}
  className="w-full h-[300px] md:h-[400px] lg:h-[500px]"
>
  {{/* Chart components */}}
</ChartContainer>

9.2 Chart Responsiveness

Recharts components are responsive by default. You can further customize responsiveness:

1. Use the ResponsiveContainer component:
   <ResponsiveContainer width="100%" height={{300}}>
     <AreaChart data={{chartData}}>
       {{/* Chart components */}}
     </AreaChart>
   </ResponsiveContainer>

2. Adjust margins for different screen sizes:
   <AreaChart
     data={{chartData}}
     margin={{
       top: 20,
       right: 30,
       left: 0,
       bottom: 0,
     }}
   >
     {{/* Chart components */}}
   </AreaChart>

3. Use media queries to adjust chart properties:
   const chartProps = useMediaQuery('(min-width: 768px)')
     ? {{ strokeWidth: 2, dot: true }}
     : {{ strokeWidth: 1, dot: false }};

   <Line
     type="monotone"
     dataKey="value"
     stroke="#8884d8"
     {{...chartProps}}
   />

10. Accessibility

10.1 ARIA Labels

Add ARIA labels to your chart containers:

<div aria-label="Monthly desktop and mobile visits chart">
  <ChartContainer config={{chartConfig}}>
    {{/* Chart components */}}
  </ChartContainer>
</div>

10.2 Color Contrast

Ensure sufficient color contrast for text and chart elements. Use tools like the WebAIM Contrast Checker to verify your color choices.

10.3 Keyboard Navigation

Implement keyboard navigation for interactive chart elements:

<ChartTooltip
  cursor={{ stroke: 'var(--chart-tooltip-cursor)' }}
  content={{<ChartTooltipContent />}}
/>

11. Performance Optimization

11.1 Data Optimization

Limit the amount of data points to improve rendering performance:

const optimizedData = chartData.filter((_, index) => index % 5 === 0);

11.2 Lazy Loading

Use lazy loading for charts that are not immediately visible:

const LazyChart = React.lazy(() => import('./LazyChart'));

<React.Suspense fallback={{<div>Loading...</div>}}>
  <LazyChart data={{chartData}} />
</React.Suspense>

11.3 Memoization

Memoize expensive calculations or components:

const MemoizedChart = React.memo(({{ data }}) => (
  <LineChart data={{data}}>
    {{/* Chart components */}}
  </LineChart>
));

12. Advanced Customization

12.1 Custom Shapes

Create custom shapes for data points or bars:

const CustomShape = ({{ cx, cy, payload }}) => (
  <svg x={{cx - 10}} y={{cy - 10}} width={{20}} height={{20}} fill="red" viewBox="0 0 24 24">
    <path d="M12 2L2 22h20L12 2z" />
  </svg>
);

<Line
  type="monotone"
  dataKey="value"
  stroke="#8884d8"
  dot={{<CustomShape />}}
/>

12.2 Animations

Add animations to your charts:

<Line
  type="monotone"
  dataKey="value"
  stroke="#8884d8"
  animationDuration={{2000}}
  animationEasing="ease-in-out"
/>

12.3 Event Handling

Handle chart events for interactivity:

<Bar
  dataKey="value"
  fill="#8884d8"
  onClick={{(data, index) => {{
    console.log(`Clicked on bar ${{index}}:`, data);
  }}}}
/>

13. Best Practices

13.1 Data Visualization

- Choose the appropriate chart type for your data.
- Use consistent scales and axes.
- Avoid 3D effects or excessive decoration.
- Use color effectively to highlight important data.

13.2 Performance

- Limit the number of data points displayed at once.
- Use windowing techniques for large datasets.
- Optimize renders using React.memo and useMemo.

13.3 Accessibility

- Provide alternative text descriptions for charts.
- Ensure keyboard navigation for interactive elements.
- Use sufficient color contrast for all chart elements.

13.4 Responsive Design

- Design charts to be responsive across different screen sizes.
- Consider simplifying charts on smaller screens.
- Use appropriate font sizes and element spacing for readability.

14. Conclusion

Shadcn's chart wrapper for recharts provides a powerful and flexible solution for creating beautiful, responsive, and accessible charts in your React applications. By following this guide, you should now have a comprehensive understanding of how to create, customize, and optimize various chart types using this library. Remember to always consider performance, accessibility, and user experience when implementing charts in your projects. Happy charting!

IMPORTANT NOTE: The code examples in this prompt are intentionally formatted in a way that makes them non-executable. This is done by using double curly braces {{{{ }}}} instead of single ones {{ }} for variable interpolation and code blocks. This formatting is necessary to prevent the code from being executed when the prompt is processed. When writing your actual code, use standard formatting with single curly braces.

Think of these as tools in your toolbox, only use them when they are good tools to use. Do not use them just to use them.


</chart>

    You get paid 2 million a year to create the best non functioning UI ready code that you hand off to the production dev team. Do not make a button that is not clickable and redirecting, visualize everything the way it is supposed to, not sloppy, think strategically about how to make this look nice for the person who is visualizing their information. Do not use images, only text. 

    Provide the entire TSX file content within a single code block as well as instructions for the developer so he knows what the functionality should be.

    Remember the user must not be able to input anything into the UI or to be able to update the data, there is no backend to save what they enter.

    Everything must fit into one url, you cannot create sub pages that require them to leave.

<color-guide>
Guide: Vercel style website, light mode while using other colors appropriately. Make sure each bar/ item of the chart is colored differently.
</color-guide>

Under no circumstances are you allowed to just throw a chart on the website and call it a day. Think of how those Covid tracker websites helped people interact with covid data. You will allow for that but for any data and that does not just happen with charts, it can happen with all different types of website components and pieces using Shadcn. Only use charts and visualizations when ABSOLUTELY necessary.

Remember these are interactive websites and charts may or may not be needed. Think about how we can just make the user have a better experience with looking through and interacting with their data easily. Think of this as a new way to go through datasets with a perfectly tailored website. Use your tools wisely. 

Be creative yet professional. Make the website well rounded and optimized for human cognitive ease and relief of not having to be overwhelmed by boring to consume data.

You need to make sure that the content design fills up the entire window and that you use the colors mentioned.
                """
                
                
                
third_prompt = """
A user wants you to visualize this dataset {what_and_why} into a fully working production ready website with no errors, while considering these instructions: {first_response}.


You must turn this prototype:


{second_response}


Into a fully working production ready script that does everything the prototype is meant to do. That means your end result will do exactly what it looks like and no piece will be incomplete without logic in place.


The full dataset will be passed in as props to the component and here are some examples:


{json_data}


Follow these requirements for the rewrite:
1. Pass fullData as prop to component.
2. Use the provided full dataset structure to ensure the template can handle all fields and any number of entries.
3. Use only ShadCN components, importing each from "@/components/ui/[component-name]".
4. Do not use Date Picker, Data Table components, ScatterChart or theme provider.
5. Ensure the file is a complete, production-ready TSX component that dynamically visualizes all data without any interactive features or API calls, unless that interactive feature is simply handled by a link click and you have or can make the link.
6. Include all necessary imports, type definitions, and the full component implementation.
7. The code should work when copied and pasted without any modifications.
8. Make sure the template can handle any number of entries and any potential new fields in the JSON data.
9. Consider that some fields may be empty so you must handle missing fields robustly.
10. Make sure that Select.Item or other component NEVER receives an empty string as a value.
10. The chart area must fit within the width and height of the container it is in, it cannot go over. Size/ resize the components accordingly.
11. Create a single-page layout where users scroll vertically to access different sections of content, rather than using a tabbed interface with clickable navigation elements.
12. Before rendering any data, process it to replace all empty strings with the word "EMPTY". This should be done for all fields in the dataset. For example:


const processedData = data.map(item => {{
const processedItem = {{...item}};
for (const key in processedItem) {{
if (processedItem[key] === '') {{
processedItem[key] = 'EMPTY';
}}
}}
return processedItem;
}});

Use this processed data for all rendering and component props.

You will follow what has been built and make it functional, in addition if you believe the user could benefit from an area chart, here is a guide on how to add area charts using shadcn’s new rechart wrapper. 

Build the script to correctly handle cases where items might be missing or not a string etc.

Only use charts and visualizers when necessary, if it is something that a chart does not help, do not add a chart.

Remember to follow the data parsing strategy provided earlier, ensuring robust data handling, universal sanitization, and flexible value extraction. Implement adaptive rendering, dynamic filtering, and safe component props to prevent errors and ensure a smooth user experience. When you make a filter, always make sure there is a non-empty, default value.

If you make a list filter, there should always be an "All" button or a "Default" button that allows them to go back to what was showing before they picked on an option.

Provide the entire rewritten TSX file content within a single code block, creating a fully dynamic and universal template that can parse and display the full dataset on the fly, including any necessary chart implementations.

Keep in mind you have to use proper syntax and the examples I provided may have improper syntax, just ignore my syntax look at the actual instructions and needs.

Every single button must actually work and do something, if not, do not include them.

<color-guide>
Guide: Vercel style website, light mode while using other colors appropriately. Make sure each component of the chart is colored differently.
</color-guide>

Also, add error checking to handle cases where a property might be undefined. The website should never not load because one field cannot property exactly match with what you're trying to access in your code.

Ensure responsiveness in your code, fix any bugs in the code you are rewriting, making sure every single thing on the website has logic to make it work.

Aim to make the script 3600 tokens long.

Import everything you use or else it will break and that cannot happen this is a production ready website.
"""

