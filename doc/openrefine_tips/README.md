# OpenRefine Reconciliation Fundamentals

- Refer to [OpenRefine Manual](https://openrefine.org/docs/manual/reconciling) for all OpenRefine reconciliation functions.
- Useful YouTube link: [YouTube Tutorial](https://www.youtube.com/watch?v=wfS1qTKFQoI&ab_channel=WikimedianinResidence-UniversityofEdinburgh)
- We currently use only the WikiData reconciliation service for all works.

# Enhances OpenRefine Capacity

- Refer to [OpenRefine Manual](https://openrefine.org/docs/manual/installing#increasing-memory-allocation)
- You must adjust the memory size before working with large files.
- Recommend size is 8GB (8192MB), choose a capable machine to work.

#  Extracting and Applying Steps

### Extracting
- You can extract a sequence of steps in OpenRefine to facilitate your workflow.
![extracting](./assets/01.png)
- Select a sequence of steps you want to keep
![extracting](./assets/02.png)
- A .json file should appear in your browswer's download folder. This contains all the steps you chose. Keep this for further use.
> Do not change what's inside that file unless you know what you're doing.

### Applying
- You can apply the sequence of steps that you kept.
![extracting](./assets/03.png)
- Choose the .json file that contains the steps you want to perform on your project.
![extracting](./assets/04.png)
![extracting](./assets/05.png)
![extracting](./assets/06.png)
- Now wait until OpenRefine is finished, and the sequence of steps will be applied.
