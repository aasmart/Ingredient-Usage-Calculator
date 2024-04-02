# Ingredient Usage Calculator 
A program I wrote for a palm oil reduction product. This program attempts to estimated the amount of ingredients contained in a product based on its volume and ingredient list.

## Features
- Estimated the palm oil in a product. This takes into account the ordering of ingredients in the ingredient list, sub ingredients, "may contain", and "contains less than x% of". A custom ingredients weight file can be fed to modify how much each time contributes to the total estimated calculation. This "reweight" can be applied to non-target ingredients without impacting the target estimation score.
- (enable with optional command flag) Grams per dollar calculation
- (enable with optional command flag) A product "score" based on an items ingredients. This metric just scores a product on "how good it is" based on the ingredient weights

## Usage
Run the `palm_calc` script with the `--help` flag enabled to learn how to use the program.

### Ingredient Weights
Ingredient weights are set in a CSV file in the following format:
`ingredient,weight,use_for_consumption`

The ingredient column is the name of the ingredient to target (e.g. "palm"). The weight is a scalar factor that can be positive or negative (e.g. "-0.5"). The "Use For Consumption" is "true" or "false", and should be true when an ingredient should contribute to the total estimated consumption of an ingredient. As a simple example:
```
ingredient,weight,use_for_consumption
palm,0.5,true
flour,-0.01,false
```

## Disclaimer
This estimation is by no means perfect, and results should be compared with the nutrition information of real products to calibrate the results and/or to make manual adjustments to the results.

## Contributing
Feel free to contribute and make my (questionable) code a little better!
