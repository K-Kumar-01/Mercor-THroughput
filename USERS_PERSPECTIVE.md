# 🧠 Classification Proxy – Developer Notes

Hi Team, thanks for providing me a chance to have a go at the throughput optimization challenge. It was fun and daunting(explained below) at the same time.

## Approach used
- Since the current approach was blocking the thread, the main idea was to execute parallely.
- This is done using batching and futures.
- The second idea was to use caching to return the result for requests already processed earlier.
    - This is even evident in the real world systems, where commonly used queries are cached.

## Weakeness

Working with apis primarily in js, I have a habit of running the server using nodemon. As a result of this, midway during the test, I forgot to restart the proxy server. Due to which several algorithms which I wrote were giving wrong results. The numbers mentioned in the document don't reflect the real time taken.

I would also like to clarify that I used AI tools for the code writing, but I am well aware of the code and provide a walkthrough as required. 


## Thanks for taking the time to read this.