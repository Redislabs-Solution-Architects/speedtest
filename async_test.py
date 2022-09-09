import asyncio
from redis import asyncio as aioredis
from redis.commands.search.field import TagField, NumericField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from time import perf_counter_ns

TEST_ITERATIONS = 10000
KEYS = 10000

r = aioredis.from_url('redis://localhost')

async def time_func(func, *args):
    # Execute a function and measure its execution time (nanoseconds)
    t1 = perf_counter_ns()
    result = await func(*args)
    t2 = perf_counter_ns()
    duration = t2 - t1
    return result, duration

# clean up db for test
async def load():
    await r.flushdb()
    pipe = r.pipeline()
    #insert keys into each prefix
    for i in range(KEYS):
        pipe.json().set(f'authNum:{i}:{i}:{i}', '$', {"acct_num":i, "au_tran_id":i, "au_auth_cd":i})
        pipe.json().set(f'authTag:{i}:{i}:{i}', '$', {"acct_num":str(i), "au_tran_id":str(i), "au_auth_cd":str(i)})
        pipe.json().set(f'authTxt:{i}:{i}:{i}', '$', {"acct_num":str(i), "au_tran_id":str(i), "au_auth_cd":str(i)})

    # set up three indices; one for each of the prefixes
    numSchema = ( NumericField('$.acct_num', as_name='acct_num'),
                NumericField('$.au_tran_id', as_name='au_tran_id'),
                NumericField('$.au_auth_cd', as_name='au_auth_cd'))
    pipe.ft('numIdx').create_index(numSchema, 
        definition=IndexDefinition(index_type=IndexType.JSON, prefix=['authNum:']))

    tagSchema = ( TagField('$.acct_num', as_name='acct_num'),
                TagField('$.au_tran_id', as_name='au_tran_id'),
                TagField('$.au_auth_cd', as_name='au_auth_cd'))
    pipe.ft('tagIdx').create_index(tagSchema, 
        definition=IndexDefinition(index_type=IndexType.JSON, prefix=['authTag:']))

    txtSchema = ( TextField('$.acct_num', as_name='acct_num'),
                TextField('$.au_tran_id', as_name='au_tran_id'),
                TextField('$.au_auth_cd', as_name='au_auth_cd'))
    pipe.ft('txtIdx').create_index(txtSchema, 
        definition=IndexDefinition(index_type=IndexType.JSON, prefix=['authTxt:']))
    
    await pipe.execute()

async def test():
    ave_num_exec = 0
    ave_tag_exec = 0
    ave_txt_exec = 0
    for i in range(1, TEST_ITERATIONS+1):
        # calc ave execution time for the numeric search
        result, duration = await time_func(r.ft('numIdx').search, Query('@acct_num:[123 123]'))
        assert result.total == 1
        ave_num_exec = round(ave_num_exec + 
            (duration - ave_num_exec)/i, 3)

        # calc ave execution time for the tag search
        result, duration = await time_func(r.ft('tagIdx').search, Query('@acct_num:{123}'))
        assert result.total == 1
        ave_tag_exec = round(ave_tag_exec + 
            (duration - ave_tag_exec)/i, 3)

        # calc ave execution time for the text search
        result, duration = await time_func(r.ft('txtIdx').search, Query('@acct_num:123'))
        assert result.total == 1
        ave_txt_exec = round(ave_txt_exec + 
            (duration - ave_txt_exec)/i, 3)

    print(f'Average num search execution time: {ave_num_exec} ns')
    print(f'Average tag search execution time: {ave_tag_exec} ns')
    print(f'Average txt search execution time: {ave_txt_exec} ns')

asyncio.run(test())