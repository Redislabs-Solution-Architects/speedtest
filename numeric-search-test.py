# Author Joey Whelan

from typing import Callable
from redis import Connection, from_url
from redis.commands.search.field import Field, TagField, NumericField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from time import perf_counter_ns
from multiprocessing import Pool, cpu_count
from argparse import ArgumentParser, ArgumentTypeError
import pandas as pd
from enum import Enum
import random


REDIS_URL:str  = 'redis://localhost:6379'   # default Redis connect string
ITERATIONS: int = 100000                    # default number of test iterations (seaches)
NKEYS:int  = 1000000                        # default number of keys (each: tag, text, numeric)
PROCESSES: int = cpu_count() - 1            # number of multiprocesses to be used
MAX_DIGITS: int = 10                        # max of digits for the field
connection: Connection = None               # global Redis connection

class FIELD_TYPE(Enum):
    NUMERIC = 1
    TAG = 2
    TEXT = 3

def multi_test(args: dict) -> pd.DataFrame:
    """ Function to launch tests.  Utilizes Python multiprocessing for Redis data load and search iterations.
        Parameters
        -----------
        args - command argument params

        Returns
        -------
        Pandas Dataframe with test summary
    """    
    global connection
    connection = from_url(args.url)
    connection.flushdb()

    create_index('numIdx', FIELD_TYPE.NUMERIC)
    create_index('tagIdx', FIELD_TYPE.TAG)
    create_index('txtIdx', FIELD_TYPE.TEXT)
    multi_load(args.nkeys)
    num_times: list[int] = []   #lists to hold test results (search exec durations)
    tag_times: list[int] = []
    txt_times: list[int] = []

    # map of number of iterations for each worker
    iterations: list[int] = [args.iterations // PROCESSES for i in range(PROCESSES)]
    iterations[0] += args.iterations % PROCESSES

    with Pool(PROCESSES) as pool:
        for nums, tags, texts in pool.map(test_worker, iterations):
            num_times.extend(nums)
            tag_times.extend(tags)
            txt_times.extend(texts)
    
    
    df = pd.DataFrame({"Numeric": num_times, "Tag": tag_times, "Text": txt_times})
    df = df.describe(percentiles=[.1, .9]).loc[['mean', '10%', '50%', '90%']].div(1000000)
    
    return df.rename(index={
        'mean':'Ave (ms)', 
        '10%': '10% (ms)', 
        '50%': '50% (ms)',
        '90%': '90% (ms)'
    })

def test_worker(iterations: int) -> tuple[list, list, list]:
    """ Multiprocessing function for test iterations.  
        Parameters
        -----------
        iterations - number of search iterations to execute

        Returns
        -------
        tuple containing lists of tag, text, and numeric search execution durations
    """   
    num_times: list[int] = []
    tag_times: list[int] = []
    txt_times: list[int] = []

    for i in range(1, iterations+1):
        rnd: int = random.randint(0, int('9' * MAX_DIGITS))
        # calc ave execution time for the numeric search
        duration: int = time_func(connection.ft('numIdx').search, Query(f'@field:[{rnd} {rnd}]'))
        num_times.append(duration)

        # calc ave execution time for the tag search
        duration = time_func(connection.ft('tagIdx').search, Query(f'@field:{{{rnd}}}'))
        tag_times.append(duration)

        # calc ave execution time for the text search
        duration = time_func(connection.ft('txtIdx').search, Query(f'@field:{rnd}'))
        txt_times.append(duration)
    return num_times, tag_times, txt_times

def time_func(func: Callable, *args: Query) -> int:
    """ Multiprocessing function for test iterations.  
        Parameters
        -----------
        func - Redis search command
        args - Redis Query param

        Returns
        -------
        execution time (nanoseconds) of the search command
    """  
    t1 = perf_counter_ns()
    func(*args)
    t2 = perf_counter_ns()
    duration = t2 - t1
    return duration

def multi_load(total_keys: int) -> None:
    """ Function for loading test keys into Redis.  Kicks off a multiprocessing function 
        Parameters
        -----------
        total_keys - total number of keys to be created, each, for text, tag, and numeric types
    """  
    keys = [total_keys // PROCESSES for i in range(PROCESSES)]
    keys[0] += total_keys % PROCESSES
    with Pool(PROCESSES) as pool:
        pool.map(load_worker, keys)

def load_worker(keys: int) -> None:
    """ Multiprocessing worker function for loading test keys into Redis.
        Parameters
        -----------
        keys - total number of keys to be created by this worker
    """  
    global connection
    pipe = connection.pipeline()
    for i in range(keys):
        val = random.randint(0, int('9' * MAX_DIGITS))
        pipe.json().set(f'keyNum:{val}', '$', {"field":val})
        pipe.json().set(f'keyTag:{val}', '$', {"field":str(val)})
        pipe.json().set(f'keyTxt:{val}', '$', {"field":str(val)})
    pipe.execute()

def create_index(idx_name: str, field_type: FIELD_TYPE) -> None:
    """ Multiprocessing worker function for loading test keys into Redis.
        Parameters
        -----------
        idx_name - name of index
        field_type - enum of index field type
    """  
    global connection
    schema: Field = None
    idx_def: IndexDefinition = None

    match field_type:
        case FIELD_TYPE.NUMERIC:
            schema = NumericField('$.field', as_name='field')
            idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['keyNum:'])
        case FIELD_TYPE.TAG:
            schema = TagField('$.field', as_name='field')
            idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['keyTag:'])
        case FIELD_TYPE.TEXT:
            schema = TextField('$.field', as_name='field')
            idx_def = IndexDefinition(index_type=IndexType.JSON, prefix=['keyTxt:'])
    connection.ft(idx_name).create_index(schema, definition=idx_def)

def check_arg(value: str) -> int:
    """ Arg parser validation of size params
        Parameters
        ----------
        value - string representing number 

        Returns
        -------
        int - input value casted to int
    """
    ival: int = int(value)
    if ival < 1 or ival > 1000000:
        raise ArgumentTypeError('size of fields must be between 1 and 15')
    return ival

if __name__ == '__main__':
    parser = ArgumentParser(description='Redis numeric search speed comparator')
    parser.add_argument('--url', required=False, type=str, default=REDIS_URL,
        help='Redis URL connect string')
    parser.add_argument('--nkeys', required=False, type=check_arg, default=NKEYS,
        metavar="[1,10000000]",  help='Number of unique keys to be created and indexed')
    parser.add_argument('--iterations', required=False, type=check_arg, default=ITERATIONS,
        metavar="[1,10000000]", help='Number of test iterations')
    args = parser.parse_args()
    
    result = multi_test(args)
    print(f'Num keys:{args.nkeys}, Test iterations:{args.iterations}')
    print(result.to_markdown())
    