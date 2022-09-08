import redis
from redis.commands.search.field import TagField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from time import perf_counter_ns

TEST_ITERATIONS = 10000
ave_num_exec = 0
ave_tag_exec = 0

def time_func(func, *args):
    # Execute a function and measure its execution time (nanoseconds)
    t1 = perf_counter_ns()
    result = func(*args)
    t2 = perf_counter_ns()
    duration = t2 - t1
    return result, duration

# clean up db for test
r = redis.Redis()
try:
    r.ft('numIdx').dropindex()
    r.ft('tagIdx').dropindex()
except Exception:
    pass

# set up two JSON keys; one with numeric fields, the other str
r.json().set('authNum:123:456:789', '$', {"acct_num":123, "au_tran_id":456, "au_auth_cd":789})
r.json().set('authTag:123:456:789', '$', {"acct_num":"123", "au_tran_id":"456", "au_auth_cd":"789"})

# set up two indices; one for each of the prefixes
numSchema = ( NumericField('$.acct_num', as_name='acct_num'),
            NumericField('$.au_tran_id', as_name='au_tran_id'),
            NumericField('$.au_auth_cd', as_name='au_auth_cd'))
r.ft('numIdx').create_index(numSchema, 
    definition=IndexDefinition(index_type=IndexType.JSON, prefix=['authNum:']))
tagSchema = ( TagField('$.acct_num', as_name='acct_num'),
            TagField('$.au_tran_id', as_name='au_tran_id'),
            TagField('$.au_auth_cd', as_name='au_auth_cd'))
r.ft('tagIdx').create_index(tagSchema, 
    definition=IndexDefinition(index_type=IndexType.JSON, prefix=['authTag:']))

for i in range(1, TEST_ITERATIONS+1):
    # calc ave execution time for the numeric search
    result, duration = time_func(r.ft('numIdx').search, Query('@acct_num:[123 123]'))
    assert result.total == 1
    ave_num_exec = round(ave_num_exec + 
        (duration - ave_num_exec)/i, 3)

    # calc ave execution time for the tag search
    result, duration = time_func(r.ft('tagIdx').search, Query('@acct_num:{123}'))
    assert result.total == 1
    ave_tag_exec = round(ave_tag_exec + 
        (duration - ave_tag_exec)/i, 3)

print(f'Average numeric search execution time: {ave_num_exec} ns')
print(f'Average tag search execution time: {ave_tag_exec} ns')