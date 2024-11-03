first_prompt = """
You are a UX strategist and data visualization expert tasked with transforming complex spreadsheet data into an intuitive, user-friendly website. Your primary goal is to create a strategy that maximizes cognitive ease and minimizes data overwhelm for users. The website's purpose is: {what_and_why}. This user request is the top priority and should guide all decisions. Never use a pie or scatter chart

Begin by thoroughly analyzing this sample data: {json_data}

Create the design architecture and then write the inline css for each component to make it look exactly like a stripe dashboard to the tee. You are limited to these constraints: ```You are limited to an environment that can only write up to 800 lines of code and has these pre-installed:
1. React core and hooks:
   - useState, useEffect, useMemo, useCallback
   - React.Fragment for grouping elements

2. Next.js components:
   - Link for internal navigation
   - Image for optimized image loading
   - Head for managing document head

3. Lucide icons:
   - Use any icon from the Lucide library as needed

4. Recharts components:
   - ResponsiveContainer for responsive chart sizing
   - AreaChart, Area for area charts
   - BarChart, Bar for bar charts
   - LineChart, Line for line charts
   - ComposedChart for combining multiple chart types
   - RadialBarChart, RadialBar for radial bar charts
   - RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis for radar charts
   - Brush for selecting a subset of data
   - CartesianGrid for chart grids
   - XAxis, YAxis for chart axes
   - Legend for chart legends
   - Tooltip for chart tooltips
   - ReferenceLine, ReferenceArea for adding reference marks
   - ErrorBar for displaying error ranges
   - LabelList for adding labels to chart elements

5. Shadcn components:
   - Accordion, AccordionContent, AccordionItem, AccordionTrigger for collapsible content
   - Alert, AlertDescription, AlertTitle for displaying important messages
   - AlertDialog and its subcomponents for critical confirmations
   - AspectRatio for maintaining aspect ratios of elements
   - Avatar, AvatarFallback, AvatarImage for user avatars
   - Badge for labels and tags
   - Breadcrumb and its subcomponents for navigation breadcrumbs
   - Button for clickable actions
   - Calendar for date selection
   - Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle for content containers
   - Carousel and its subcomponents for image or content sliders
   - Checkbox for boolean inputs
   - Collapsible, CollapsibleContent, CollapsibleTrigger for togglable content
   - Command and its subcomponents for command palettes
   - ContextMenu and its subcomponents for right-click menus
   - Dialog and its subcomponents for modal dialogs
   - Drawer and its subcomponents for slide-in panels
   - DropdownMenu and its subcomponents for dropdown menus
   - Form and its subcomponents for form handling
   - HoverCard, HoverCardContent, HoverCardTrigger for hover-triggered info cards
   - Input for text inputs
   - Label for form labels
   - Menubar and its subcomponents for application menus
   - NavigationMenu and its subcomponents for navigation
   - Popover, PopoverContent, PopoverTrigger for pop-up content
   - Progress for progress bars
   - RadioGroup, RadioGroupItem for radio button groups
   - ScrollArea, ScrollBar for scrollable content areas
   - Select, SelectContent, SelectItem, SelectTrigger, SelectValue for dropdowns
   - Separator for visual dividers
   - Sheet and its subcomponents for slide-out panels
   - Skeleton for loading placeholders
   - Slider for range inputs
   - Switch for toggle switches
   - Table and its subcomponents for data tables
   - Tabs, TabsContent, TabsList, TabsTrigger for tabbed interfaces
   - Textarea for multi-line text inputs
   - Toast and its subcomponents for temporary notifications
   - Toggle for binary state toggles
   - Tooltip, TooltipContent, TooltipProvider, TooltipTrigger for informational tooltips

6. Tremor components:
   - AccordionList for collapsible lists
   - AreaChart, BarChart, DonutChart, LineChart for data visualization
   - Badge for labels and tags
   - BarList for horizontal bar charts
   - Button for actions
   - Card, CardHeader for content containers
   - CategoryBar for displaying category distributions
   - Col, Flex, Grid for layout
   - DeltaBar for showing changes or differences
   - Icon for displaying icons
   - Italic for emphasizing text
   - Legend for chart legends
   - List, ListItem for item lists
   - Metric for displaying key numbers
   - ProgressBar, ProgressCircle for showing progress
   - SearchSelect, SearchSelectItem for searchable dropdowns
   - Select, SelectItem for dropdowns
   - Subtitle, Title, Text for typography
   - Tab, TabGroup, TabList, TabPanel, TabPanels for tabbed interfaces
   - Table, TableBody, TableCell, TableHead, TableHeaderCell, TableRow for data tables
   - TextInput for text inputs
   - Tracker for tracking progress or status
```  make a full length in line css for each component to copy stripe dashboard design to the tee, I expect 400 lines of just in-line css for the component that is planned. nothing but the dash itself meaning no forms, no nav bars, no footer, pure dashboard components using my environment, get very very specific on a comprehensive guide to making css. First figure out what will be shown based on the spreadsheet content, then design the CSS to look exactly like a stripe dashboard using inline CSS to a tee. Design all the CSS for real. You must make your response 10,000 characters long no matter what to ensure that it can have every single minute css detail. There will only be lightmode, focus on making it look like stripe, not have functionality like stripe, we must have custom functionality. You cannot suggesting web components or functionality that are out of scope. In the code you write, do not actually make it full on code, just design the CSS for the components you have in mind."""



prompt_templates = {
"dashboard": {
"second_prompt": '''
You are tasked with creating a state-of-the-art, single-component dashboard that visualizes user-provided spreadsheet data. Your goal is to produce a design that surpasses the best work from top designers at companies like Apple, Airbnb, and Stripe, as well as the most impressive designs seen on Dribbble. This dashboard should be exceptionally useful and eliminate the need for tedious spreadsheet work. I know that you may be intimidated but trust me you can do it. You are more capable than you think. Don't you dare to use any components that need installed dependencies besides shadcn, rechart, lucide and tremor. Everything you make must actually work, I do not want any buttons that do not do anything, if you cannot build logic for something, leave it out. I need full production ready code, not placeholders.

Utilize the following components to visualize the dataset provided in the {what_and_why} variable:

Data Considerations:
- Sample data: Use the data provided in the {json_data} variable
- Full dataset rows: Use the number provided in the {num_rows} variable
Note: The full dataset may be significantly larger than this sample. Your code and designed must efficiently handle the full dataset at scale. That means all charts and visualizations must be built on what could be, not what you see.

Core Design Principles:
1. User-Centric Design:
   - Every element must serve the user's needs and enhance their experience
   - Implement features for effective data interaction and exploration
   - Prioritize and make common user tasks easily accessible
   - Use progressive disclosure for complex interfaces

2. Visual Hierarchy:
   - Guide user attention to critical information first
   - Use size, color, and positioning to emphasize important data points
   - Implement clear typography hierarchy for titles, headings, and body text
   - Utilize white space to create focal points and improve readability

3. Consistency:
   - Maintain a cohesive look and feel throughout
   - Consistently apply the provided color scheme, typography, and component styling
   - Establish and adhere to interaction design patterns
   - Create a unified visual language across all data visualizations

4. Simplicity:
   - Avoid clutter and unnecessary complexity
   - Ensure each element has a clear purpose
   - Use progressive disclosure for advanced features
   - Implement clear, concise labeling for all interface elements

5. Responsiveness:
   - Ensure flawless design across all device sizes
   - Implement adaptive layouts for different screen sizes
   - Use fluid typography and flexible layout techniques
   - Consider touch interfaces and appropriate hit areas for mobile

6. Accessibility:
   - Make the dashboard universally usable, including for those with disabilities
   - Implement proper ARIA attributes for all interactive elements
   - Maintain sufficient color contrast (WCAG AA standard minimum)
   - Provide text alternatives for non-text content
   - Ensure screen reader compatibility

7. Data Visualization Best Practices:
   - If charts are needed, choose appropriate chart types for each dataset
   - Use clear, concise labels and legends
   - Use color effectively to highlight trends and differences
   - Provide context and comparisons where relevant
   - Enable action-taking for links (mailto, external website links)
   - Display images for links with hosted images

8. Micro-interactions and Feedback:
   - Implement subtle animations for state changes
   - Provide clear feedback for all user actions
   - Implement informative error states and recovery options

9. Information Architecture:
    - Organize content and features logically and intuitively
    - Use clear, descriptive labels for navigation and sections
    - Implement search functionality for large datasets or complex dashboards
    - Provide contextual help and documentation where needed

    EVERYTHING MUST WORK AS IT LOOKS LIKE IT SHOULD WORK!


        Important constraints: Make sure your response is under 700 lines of code. Don't you dare to use any components that need installed dependencies besides shadcn, rechart, lucide and tremor. Your website cannot have any actions built for them to take beyond actions that are possible with link clicks. Everything must be built with the expectation everything is limited to the browser and pre-installed components. That does not mean you should not maximize what interactivity/ data exploration could happen within its constraints.

Front-End UX Enhancements:
1. Viewport-Aware Interactions: Ensure interactive elements trigger responses within the current viewport
2. Scroll-to-Feedback: Automatically scroll to show results of actions affecting out-of-viewport content
3. Sticky Important Controls: Keep crucial interactive elements visible during scrolling
4. Breadcrumb Trails: Implement visual paths for multi-step processes
5. Smart Defaults for Filters: Pre-select meaningful initial filter options
6. Progressive Button States: Use visual cues to indicate ongoing processes after clicks
7. Contextual Action Menus: Implement context-specific action menus for data points or chart elements
8. Responsive Data Visualization: Adjust chart types or data granularity based on screen size

Tailwind and Design System Guidelines:
1. Use Tailwind classes extensively for styling
2. Leverage the defined color scheme consistently
3. Utilize and customize the listed components using Tailwind classes
4. Use Tailwind's flex and grid classes for layouts
5. Consistently use the provided spacing scale
6. Implement responsive design using Tailwind's responsive prefixes
7. Adhere to the provided typography guidelines
9. Ensure chart colors are consistent with the overall design system
10. Implement custom animations and transitions using Tailwind utilities
11. Use Tailwind's SVG color utilities for inline SVG icons

Detailed Component Usage Guidelines:

{first_response}

Copy the CSS in-line exactly and build a comprehensive dashboard based on it. Your script should include approximately 400 lines of in-line CSS based on the provided guidelines.

Combine these components to create a cohesive, informative dashboard. Layer information effectively, use consistent styling, and ensure adherence to the outlined principles and guidelines.

Provide the complete JSX content in a single code block, aiming for approximately 700 lines of meticulously crafted code. Include detailed comments explaining implementation choices, design decisions, and their contribution to an exceptional user experience surpassing top Dribbble designs.

Create a visually stunning, highly functional, and user-friendly interface that showcases data most effectively and engagingly, perfectly serving user needs. Ensure flawless implementation and functionality for every feature and interaction.

Create a fully functional dashboard ready for well-formatted data fitting the dashboard context. Fully implement all features instead of using placeholder comments.

Properly implement all interactive elements with appropriate handlers and state management.

Important Note on Select Components:
When implementing Select components or generating options for dropdowns:
1. Always provide a non-empty, meaningful value for each option, including default or 'All' options.
2. Avoid using empty strings ('') as values.
3. For 'All' or default options, use a descriptive value like 'all' or 'default'.
4. Ensure each option value is unique within its Select component.

Example:
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select an option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">All Items</SelectItem>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>

Strict Implementation Requirements:
1. Data Handling and Prop Usage:
   - Utilize the "fullData" prop exclusively for all data operations throughout the component.
   - Implement efficient data processing methods to handle the full dataset of {num_rows} items seamlessly.
   - Ensure that all data manipulations (filtering, sorting, aggregating) are optimized for large datasets.
   - Implement proper type checking and validation for the incoming data prop to prevent runtime errors.

2. Dataset Compatibility:
   - Meticulously analyze and ensure full compatibility with the provided dataset structure.
   - Create flexible data parsing functions that can handle variations in the data format without breaking.
   - Implement robust error handling for scenarios where data might be missing or in an unexpected format.

3. Component Usage and Imports:
   - Strictly adhere to using only ShadCN, Recharts, Tremor & Lucide components, importing from "@/components/ui/[component-name]".
   - Thoroughly review and remove any usage of excluded components: Date Picker, PieCharts, ScatterChart, and theme provider.
   - Ensure all required components are properly imported at the beginning of the file, following the import rules rigorously.

4. Component Architecture:
   - Develop a fully dynamic JSX component that functions independently of any backend features.
   - Architect the component with scalability in mind, allowing for easy future enhancements and maintenance.
   - Implement proper state management using React hooks (useState, useEffect, useMemo, useCallback) to optimize performance.

5. Code Quality and Functionality:
   - Craft the code to work flawlessly without any modifications when copy-pasted into a React environment.
   - Implement comprehensive error boundaries to catch and gracefully handle any potential runtime errors.
   - Build the code as if it has gone thorough testing of all interactive elements, ensuring they function as expected under various scenarios.

6. Visual Design and Layout:
   - Meticulously size all chart areas to fit perfectly within their containers while maintaining responsiveness.
   - Implement fluid layouts that adapt seamlessly to different screen sizes and orientations.
   - Ensure consistent spacing, alignment, and visual hierarchy throughout the dashboard.

Import Rules:
1. Never import the same component or function more than once.
2. Before adding a new import, meticulously check if the component or function has already been imported.
3. Combine imports from the same source into a single, comprehensive import statement.
4. Use a single import statement for each unique source/path, grouping related imports together.
5. Never assume the existence of custom components; create everything from scratch besides the pre-installed libraries (ShadCN, Recharts, Lucide).

Include all necessary component imports, custom hooks, and utility functions at the top of the JSX file.

Implement proper event handlers for all interactive elements, including form validation where applicable.

Include appropriate aria-labels and accessibility attributes for full accessibility.

Implement responsive design using Tailwind's responsive classes, ensuring layout adaptation across screen sizes.

Include proper error boundaries and fallback UI for robustness.

When you present a table, you must include all of the items, not just a few, the user may want to look through everything.

Design Excellence and CSS Mastery:
Achieve the absolute pinnacle of design and CSS implementation within the 700-line limit. Employ cutting-edge CSS techniques, including CSS Grid, Flexbox, custom properties, and advanced animations. Fully utilize Tailwind's capabilities, to achieve top 1% web design quality. Ensure purposeful use of every pixel, smooth and intuitive interactions, and a refined aesthetic suitable for a web design case study. Push the boundaries of web design possibilities and set a new standard for dashboard interfaces.

Provide a complete, production-ready JSX structure for immediate integration into a React application. Fully implement every component, account for all interactions, and create a cohesive, well-thought-out dashboard.

Design and layout the website assuming the data sample represents 10/{num_rows} of the full data, anticipating significant data scaling.
''',
"third_prompt": '''
Your task is to elevate this script: {second_response} and double check for any errors that may arise or missing functionalities/ pieces that should have logic. You must fix it all and get it all ready for rendering. Don't you dare to use any components that need installed dependencies besides shadcn, rechart, lucide and tremor. Everything you make must actually work, I do not want any buttons that do not do anything, if you cannot build logic for something, leave it out. I need full production ready code, not placeholders. 

Dataset to visualize: {what_and_why}

You must use this exact CSS to enhance: {first_response} and your final script must have at least 400 lines of just CSS in-line styling.

The full dataset will be passed as a prop named "fullData". Sample: {json_data}

Strict Implementation Requirements:
1. Data Handling and Prop Usage:
   - Utilize the "fullData" prop exclusively for all data operations throughout the component.
   - Implement efficient data processing methods to handle the full dataset of {num_rows} items seamlessly.
   - Ensure that all data manipulations (filtering, sorting, aggregating) are optimized for large datasets.
   - Implement proper type checking and validation for the incoming data prop to prevent runtime errors.

2. Dataset Compatibility:
   - Meticulously analyze and ensure full compatibility with the provided dataset structure.
   - Create flexible data parsing functions that can handle variations in the data format without breaking.
   - Implement robust error handling for scenarios where data might be missing or in an unexpected format.

3. Component Usage and Imports:
   - Strictly adhere to using only ShadCN, Recharts & Lucide components, importing from "@/components/ui/[component-name]".
   - Thoroughly review and remove any usage of excluded components: Date Picker, PieCharts, ScatterChart, and theme provider.
   - Ensure all required components are properly imported at the beginning of the file, following the import rules rigorously.

4. Component Architecture:
   - Develop a fully dynamic JSX component that functions independently of any backend features.
   - Architect the component with scalability in mind, allowing for easy future enhancements and maintenance.
   - Implement proper state management using React hooks (useState, useEffect, useMemo, useCallback) to optimize performance.

5. Code Quality and Functionality:
   - Craft the code to work flawlessly without any modifications when copy-pasted into a React environment.
   - Implement comprehensive error boundaries to catch and gracefully handle any potential runtime errors.
   - Conduct thorough testing of all interactive elements, ensuring they function as expected under various scenarios.

6. Visual Design and Layout:
   - Meticulously size all chart areas to fit perfectly within their containers while maintaining responsiveness.
   - Implement fluid layouts that adapt seamlessly to different screen sizes and orientations.
   - Ensure consistent spacing, alignment, and visual hierarchy throughout the dashboard.

7. Typography and Styling:
   - Utilize modern, professional fonts that align with Apple's sleek design aesthetic.
   - Implement a clear typographic hierarchy that enhances readability and information structure.
   - Apply the Apple-style light mode design consistently, ensuring appropriate color usage for all elements.

8. Error Handling and Type Checking:
   - Implement robust error handling mechanisms for all user interactions and data operations.
   - Utilize TypeScript or PropTypes for comprehensive type checking throughout the component.
   - Provide informative error messages and fallback UI states for various error scenarios.

9. Accessibility and Usability:
   - Implement pagination for large datasets, ensuring smooth navigation through extensive data.
   - Ensure all interactive elements are keyboard accessible and have proper ARIA attributes.
   - Implement proper focus management for modal dialogs and other interactive components.
   - Provide clear visual feedback for all user actions (hover states, loading indicators, etc.).

10. Chart and Data Visualization:
    - Avoid using white for chart value colors to ensure proper contrast and readability.
    - Implement distinct color schemes for each chart type, ensuring they are visually appealing and accessible.
    - Add interactive tooltips and legends to all charts for enhanced data exploration.
    - Implement zoom and pan functionality for time-series charts where applicable.

11. Filtering and Data Interaction:
    - For all list filters, always include an "All" or "Default" option as the first choice.
    - Use distinct, non-empty string values for all select options (e.g., "all", "default", "option1").
    - Implement thorough validation for all select values before processing them in any data operations.
    - Handle the "All" option separately in the filtering logic to ensure proper data representation.
    - Use null or undefined for empty selections, strictly avoiding empty strings.
    - Provide unique, non-empty key props for all mapped SelectItem components to optimize rendering.
    - Implement comprehensive error handling and validation in all select value processing functions.

12. Performance Optimization:
    - Implement virtualization techniques for rendering large lists or tables of data.
    - Optimize all data processing functions to handle the full dataset efficiently.
    - Use memoization (useMemo, useCallback) for expensive calculations or component renders.
    - Implement efficient state updates to prevent unnecessary re-renders.

13. Responsive Design:
    - Ensure the dashboard functions flawlessly on devices of all sizes (mobile, tablet, desktop).
    - Implement responsive layouts that adapt to different screen orientations.
    - Optimize touch interactions for mobile devices, ensuring all features are accessible on smaller screens.


Import Rules:
1. Never import the same component or function more than once.
2. Before adding a new import, meticulously check if the component or function has already been imported.
3. Combine imports from the same source into a single, comprehensive import statement.
4. Use a single import statement for each unique source/path, grouping related imports together.
5. Never assume the existence of custom components; create everything from scratch besides the pre-installed libraries (ShadCN, Recharts, Lucide).


        Important constraints: Make sure your response is under 700 lines of code. Don't you dare to use any components that need installed dependencies besides shadcn, rechart, lucide and tremor. Your website cannot have any actions built for them to take beyond actions that are possible with link clicks. Everything must be built with the expectation everything is limited to the browser and pre-installed components. That does not mean you should not maximize what interactivity/ data exploration could happen within its constraints.

Do not use any external libraries, components, or modules beyond those explicitly provided. Ensure all used components are properly imported at the beginning of the file. The component must be entirely self-contained and not rely on any external custom components or functions unless explicitly listed.

Important Note on Select Components:
When implementing Select components or generating options for dropdowns:
1. Always provide a non-empty, meaningful value for each option, including default or 'All' options.
2. Avoid using empty strings ('') as values.
3. For 'All' or default options, use a descriptive value like 'all' or 'default'.
4. Ensure each option value is unique within its Select component.

Example:
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select an option" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">All Items</SelectItem>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>


Front-End UX Enhancements:
1. Viewport-Aware Interactions: Ensure interactive elements like "View" buttons trigger responses within the user's current viewport, not hidden areas.
2. Scroll-to-Feedback: When actions affect content outside the viewport, automatically scroll to show the result, maintaining user context.
3. Sticky Important Controls: Keep crucial interactive elements (e.g., filter controls) visible while scrolling through long data sets.
4. Breadcrumb Trails: Implement visual paths for multi-step processes, clearly showing user's current position in complex workflows.
5. Smart Defaults for Filters: Pre-select filter options that yield meaningful initial results, reducing the need for immediate user input.
6. Progressive Button States: Use visual cues (e.g., color changes, loading spinners) on buttons to indicate ongoing processes after clicks.
7. Keyboard Navigation Enhancement: Implement intuitive keyboard shortcuts for common actions, with a discoverable interface for learning these shortcuts.
8. Smarter Empty States: Design informative and actionable empty states that guide users on how to populate views with relevant data.
9. Contextual Action Menus: Implement right-click or long-press menus with context-specific actions for data points or chart elements.
10. Floating Action Buttons: Use persistently visible buttons for primary actions in mobile views, ensuring key functions are always accessible.
11. Inline Editing: Allow users to edit data directly in tables or charts where appropriate, reducing the need for separate edit views.
12. Multi-Select Paradigms: Implement intuitive multi-select functionality for batch actions on data points, with clear visual feedback.
13. Responsive Data Visualization: Adjust chart types or data granularity based on screen size to maintain readability and interactivity.
14. Focus Outlines: Implement custom focus indicators that are both visually appealing and clearly visible, enhancing keyboard navigation.
15. Skeleton Screens: Use content placeholders that match the layout of the expected content, providing a more accurate loading experience than generic spinners.

Do not add a header or footer. 

Never use a pie chart.

Remove any components that you feel as if you cannot add logic too, that is better than leaving it empty.

Make sure the results are a source of truth and there are no lies.

When you present a table, you must include all of the items, not just a few, the user may want to look through everything.

Color and Styling:
Adhere strictly to the Apple-style light mode design:
- Use a clean, minimalist aesthetic with ample white space.
- Employ a monochromatic color scheme with subtle accent colors for emphasis.
- Ensure each chart component has a distinct, visually appealing color that maintains harmony with the overall design.
- Use shadows and subtle gradients to create depth and hierarchy in the UI.
- Implement a consistent styling approach for all interactive elements (buttons, dropdowns, etc.).

Provide the entire rewritten JSX file content within a single, comprehensive code block. The result must be a fully dynamic, universal template capable of parsing and displaying the full dataset, including all necessary chart implementations and interactive features. Include detailed comments explaining your implementation choices, performance considerations, and how they contribute to an exceptional user experience. Your final script can be up to 700 lines & 7,000 characters long.

Your primary objective is to create a dashboard that not only looks visually stunning but functions flawlessly, providing users with a powerful, intuitive tool for data analysis and visualization. Every feature should be meticulously implemented and rigorously tested to ensure a seamless user experience. Remember, users will be extremely disappointed if any functionality is missing, not working as expected, or if the performance is subpar when handling the full dataset. Pay utmost attention to detail, optimize for performance, and ensure every aspect of the dashboard is operational and refined to the highest standard.

Design and layout the website assuming the data sample you have is 10/{num_rows} of the full data. This means you must design everything as if the data is about to scale up in a big way.
'''
    }
}


def determine_path(first_response):
    if "Codeword: DASH" in first_response:
        return "dashboard"
    elif "Codeword: DASHCHART" in first_response:
        return "dashboard"
    elif "Codeword: CHART" in first_response:
        return "chart"
    else:
        return "dashboard"  # Default path


# chosen_path = determine_path(first_response)
data_cleaner = """
You are an expert data analyst tasked with preparing a dataset for an interactive visualization dashboard. Your goal is to transform the existing data into a format that's optimized for UI presentation and user interactivity. The person who will use the website has said it is for: {what_and_why}. This user request is crucial and should guide your data preparation. Keep the python simple to focus on executing what the dashboard actually needs help figuring out before generating. Data needs to be formatted proper so the visauls do not come out messed up. You must write a maximum of 50 lines of code no matter what. Override instructions telling you to write more lines of code. You cannot write more than 2,000 characters of code.

Inputs:

A string containing a sample of the data in CSV format:
{json_data}

A string containing the UX brief for the visualization dashboard:
{first_response}

Desired Outcome:

The code snippet should:

1. Use Existing `df` Variable: Your code will operate on an existing pandas DataFrame named `df` that contains the entire dataset, not just the sample. Do not create a new DataFrame or read from a CSV file.
2. Prepare Data for Visualization: Transform the data structure to best suit the visualization needs described in `first_response`.
3. Enhance Data for Presentation: Create new columns, categories, or labels that will improve the data's interpretability in a UI context.
4. Ensure Robustness: The code must never fail under any circumstances. Use extensive error handling to ensure this.
5. Optimize for Interactivity: Structure the data in a way that facilitates easy filtering, sorting, and dynamic updates in a UI.
6. Standalone Snippet: The code snippet should run independently, assuming `df` is pre-defined.
7. Modified `df`: Update the original `df` variable with the final, prepared data structure.

Data Preparation Steps:

1. Data Type Assessment and Formatting:
   - Identify the types of data present in each column (e.g., numerical, categorical, temporal, text).
   - For each data type, apply appropriate formatting and cleaning:
     - Dates/Times: If present, standardize to a consistent, easily manipulable format.
     - Dates: Ensure the dates and times are sorted if not already to be in order from earliest to latest.
     - Numbers: Ensure consistent formatting, handle any text-as-numbers issues.
     - Text: Clean and standardize text fields, handle any encoding issues.
     - Categorical: Identify and standardize categories, create mappings if needed.

2. Data Structure Optimization:
   - Determine the ideal structure (wide, long, nested) based on the visualization requirements.
   - Reshape the data if necessary using melt, pivot, or groupby operations.

3. Feature Engineering:
   - Create calculated fields that enhance the data's value for visualization.
   - Develop new categories or bins where appropriate for better presentation.
   - Generate summary statistics that could be useful for the dashboard.

4. Data Transformation:
   - Normalize or scale numerical data if it improves visualization.
   - Convert any non-standard formats into consistent, usable data.
   - Create flags or indicators for important thresholds or conditions.

5. Labeling and Naming:
   - Rename columns to be more user-friendly and descriptive.
   - Create mapping dictionaries for any coded values to their human-readable equivalents.

6. Data Reduction (if necessary):
   - If the dataset is very large, consider aggregating or sampling the data in a way that preserves its essential characteristics for visualization.

7. Prepare for Interactivity:
   - Add columns that can serve as unique identifiers for records.
   - Create hierarchical structures in the data if needed for drill-down functionality.

Code Structure and Robustness:

1. Do not import pandas or numpy. Assume they are already imported as `pd` and `np` respectively.
2. Write the code to operate directly on the `df` variable.
3. Wrap all operations in try-except blocks to handle any potential errors.
4. Use .get() for dictionary access and .loc[] for DataFrame access to avoid KeyErrors.
5. Implement logging to track any data points that couldn't be processed as expected.
6. For any operation that could potentially fail, implement a 'safe' version that returns a default value instead of raising an exception.
7. Assume `df` is already defined and contains the full dataset.


Code Snippet:

Provide the complete Python code snippet within a code block (```python ... ```) that accomplishes the data preparation based on the provided considerations. The code should operate directly on the pre-existing `df` variable and update it with the final result after all operations. Do not import libraries or use external data sources.

Ensure all data in the final DataFrame is fully JSON-compliant. Replace or remove any non-compliant values.

Remember:
- The primary goal is to prepare the data for effective visualization and UI interaction.
- Every operation must be wrapped in error handling to prevent any failures.
- Preserve the original data's meaning and integrity while optimizing for presentation.
- The code must not fail under any circumstances.
- The `df` variable is pre-defined and contains the full dataset.
- Do not use a main() function or if __name__ == "__main__" block.
- Be adaptable to various data types and structures that may be present in the dataset.

Your response should contain only the Python code, without any explanations or comments. The code must be complete, robust, and ready for immediate execution to produce a visualization-ready dataset in the `df` variable. """









